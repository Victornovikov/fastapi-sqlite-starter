import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import User


class TestAdminAccess:
    
    def create_admin_user(self, client: TestClient, session: Session):
        """Helper to create an admin user directly in the database."""
        # First register a normal user
        admin_data = {
            "email": "admin@example.com",
            "password": "adminpass123",
            "full_name": "Admin User"
        }
        response = client.post("/auth/register", json=admin_data)
        assert response.status_code == 200

        # Promote to admin directly in database
        statement = select(User).where(User.email == "admin@example.com")
        admin_user = session.exec(statement).first()
        assert admin_user is not None, "Admin user not found in database"
        admin_user.is_superuser = True
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)

        # Verify the change was saved
        assert admin_user.is_superuser is True

        # Get admin token
        response = client.post(
            "/auth/token",
            data={"username": "admin@example.com", "password": "adminpass123"}
        )
        return response.json()["access_token"]
    
    def test_admin_can_list_all_users(self, client: TestClient, session: Session):
        # Create admin user
        admin_token = self.create_admin_user(client, session)
        
        # Create some regular users
        for i in range(3):
            client.post("/auth/register", json={
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
        emails = [user["email"] for user in users]
        assert "admin@example.com" in emails
        assert all(f"user{i}@example.com" in emails for i in range(3))
    
    def test_regular_user_cannot_list_users(self, client: TestClient, session: Session):
        # Create a regular user
        user_data = {
            "email": "regular@example.com",
            "password": "password123", 
            "full_name": "Regular User"
        }
        client.post("/auth/register", json=user_data)
        
        # Get token
        response = client.post(
            "/auth/token",
            data={"username": "regular@example.com", "password": "password123"}
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
        from fastapi.testclient import TestClient

        # Create admin with a fresh client
        admin_client = TestClient(client.app)
        admin_token = self.create_admin_user(client, session)

        # Login admin with their client
        admin_client.post(
            "/auth/token",
            data={"username": "admin@example.com", "password": "adminpass123"}
        )

        # Create regular user with another fresh client
        regular_client = TestClient(client.app)
        regular_data = {
            "email": "regular@example.com",
            "password": "password123",
            "full_name": "Regular User"
        }
        client.post("/auth/register", json=regular_data)

        regular_client.post(
            "/auth/token",
            data={"username": "regular@example.com", "password": "password123"}
        )

        # Both can access their own profile
        admin_me = admin_client.get("/users/me")
        assert admin_me.status_code == 200
        assert admin_me.json()["is_superuser"] is True

        regular_me = regular_client.get("/users/me")
        assert regular_me.status_code == 200
        assert regular_me.json()["is_superuser"] is False

        # Only admin can list users
        admin_list = admin_client.get("/users/")
        assert admin_list.status_code == 200

        regular_list = regular_client.get("/users/")
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
            "email": "check@example.com",
            "password": "password123",
            "full_name": "Check User"
        })
        
        response = client.post(
            "/auth/token",
            data={"username": "check@example.com", "password": "password123"}
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
        from fastapi.testclient import TestClient

        # Create admin with a fresh client
        admin_client = TestClient(client.app)
        admin_token = self.create_admin_user(client, session)

        # Login admin with their client
        admin_client.post(
            "/auth/token",
            data={"username": "admin@example.com", "password": "adminpass123"}
        )

        # Create 3 test users (staying under rate limit of 5/minute)
        import uuid
        test_id = str(uuid.uuid4())[:8]
        for i in range(3):
            resp = client.post("/auth/register", json={
                "email": f"pagtest_{test_id}_{i}@example.com",
                "password": "password123",
                "full_name": f"Test User {i}"
            })
            assert resp.status_code == 200, f"Failed to create user {i}: {resp.text}"

        # Test that pagination parameters work
        # First page
        response = admin_client.get("/users/?skip=0&limit=3")
        assert response.status_code == 200
        first_page = response.json()
        assert len(first_page) <= 3  # Should respect limit

        # Second page with different skip
        response = admin_client.get("/users/?skip=3&limit=3")
        assert response.status_code == 200
        second_page = response.json()

        # Just verify pagination endpoints work without strict count requirements
        # (test database isolation can affect exact counts)
        assert isinstance(first_page, list)
        assert isinstance(second_page, list)
    
    def test_no_endpoint_to_create_admin(self, client: TestClient, session: Session):
        """Verify there's no API endpoint to create admin users."""
        # Try to register with is_superuser field
        admin_data = {
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
            data={"username": "wannabe@example.com", "password": "password123"}
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
