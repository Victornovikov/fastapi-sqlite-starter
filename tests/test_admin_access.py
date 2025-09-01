import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import User


class TestAdminAccess:
    
    def create_admin_user(self, client: TestClient, session: Session):
        """Helper to create an admin user directly in the database."""
        # First register a normal user
        admin_data = {
            "username": "admin",
            "email": "admin@example.com", 
            "password": "adminpass123",
            "full_name": "Admin User"
        }
        response = client.post("/auth/register", json=admin_data)
        assert response.status_code == 200
        
        # Promote to admin directly in database
        statement = select(User).where(User.username == "admin")
        admin_user = session.exec(statement).first()
        admin_user.is_superuser = True
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        # Get admin token
        response = client.post(
            "/auth/token",
            data={"username": "admin", "password": "adminpass123"}
        )
        return response.json()["access_token"]
    
    def test_admin_can_list_all_users(self, client: TestClient, session: Session):
        # Create admin user
        admin_token = self.create_admin_user(client, session)
        
        # Create some regular users
        for i in range(3):
            client.post("/auth/register", json={
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": "password123",
                "full_name": f"User {i}"
            })
        
        # Admin should be able to list all users
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 4  # admin + 3 regular users
        
        # Verify admin is in the list
        usernames = [user["username"] for user in users]
        assert "admin" in usernames
        assert all(f"user{i}" in usernames for i in range(3))
    
    def test_regular_user_cannot_list_users(self, client: TestClient, session: Session):
        # Create a regular user
        user_data = {
            "username": "regularuser",
            "email": "regular@example.com",
            "password": "password123", 
            "full_name": "Regular User"
        }
        client.post("/auth/register", json=user_data)
        
        # Get token
        response = client.post(
            "/auth/token",
            data={"username": "regularuser", "password": "password123"}
        )
        token = response.json()["access_token"]
        
        # Regular user should get 403
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_admin_vs_regular_user_access(self, client: TestClient, session: Session):
        # Create admin
        admin_token = self.create_admin_user(client, session)
        
        # Create regular user
        regular_data = {
            "username": "regular",
            "email": "regular@example.com",
            "password": "password123",
            "full_name": "Regular User"
        }
        client.post("/auth/register", json=regular_data)
        
        regular_response = client.post(
            "/auth/token",
            data={"username": "regular", "password": "password123"}
        )
        regular_token = regular_response.json()["access_token"]
        
        # Both can access their own profile
        admin_me = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_me.status_code == 200
        assert admin_me.json()["is_superuser"] is True
        
        regular_me = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert regular_me.status_code == 200
        assert regular_me.json()["is_superuser"] is False
        
        # Only admin can list users
        admin_list = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_list.status_code == 200
        
        regular_list = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        assert regular_list.status_code == 403
    
    def test_admin_field_in_user_response(self, client: TestClient, session: Session):
        # Create admin
        admin_token = self.create_admin_user(client, session)
        
        # Check that is_superuser field is included in response
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_superuser" in data
        assert data["is_superuser"] is True
        
        # Create and check regular user
        client.post("/auth/register", json={
            "username": "checkuser",
            "email": "check@example.com",
            "password": "password123",
            "full_name": "Check User"
        })
        
        response = client.post(
            "/auth/token",
            data={"username": "checkuser", "password": "password123"}
        )
        token = response.json()["access_token"]
        
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_superuser" in data
        assert data["is_superuser"] is False
    
    def test_pagination_works_for_admin(self, client: TestClient, session: Session):
        # Create admin
        admin_token = self.create_admin_user(client, session)
        
        # Create 10 users
        for i in range(10):
            client.post("/auth/register", json={
                "username": f"testuser{i}",
                "email": f"test{i}@example.com",
                "password": "password123",
                "full_name": f"Test User {i}"
            })
        
        # Test pagination
        response = client.get(
            "/users/?skip=0&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 5
        
        # Get next page
        response = client.get(
            "/users/?skip=5&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 5  # Should have at least 5 more users
    
    def test_no_endpoint_to_create_admin(self, client: TestClient, session: Session):
        """Verify there's no API endpoint to create admin users."""
        # Try to register with is_superuser field
        admin_data = {
            "username": "wannabeadmin",
            "email": "wannabe@example.com",
            "password": "password123",
            "full_name": "Wannabe Admin",
            "is_superuser": True  # This should be ignored
        }
        
        response = client.post("/auth/register", json=admin_data)
        assert response.status_code == 200
        
        # Login and check if user is actually admin
        response = client.post(
            "/auth/token",
            data={"username": "wannabeadmin", "password": "password123"}
        )
        token = response.json()["access_token"]
        
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["is_superuser"] is False  # Should not be admin
        
        # Verify they can't access admin endpoints
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
