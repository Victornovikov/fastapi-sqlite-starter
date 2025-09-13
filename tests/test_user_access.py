import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestUserAccessControl:
    
    def setup_two_users(self, client: TestClient):
        user1_data = {
            "email": "alice@example.com",
            "password": "alicepass123",
            "full_name": "Alice Smith"
        }
        
        user2_data = {
            "email": "bob@example.com",
            "password": "bobpass123",
            "full_name": "Bob Jones"
        }
        
        client.post("/auth/register", json=user1_data)
        client.post("/auth/register", json=user2_data)
        
        response1 = client.post(
            "/auth/token",
            data={"username": "alice@example.com", "password": "alicepass123"}
        )
        token1 = response1.json()["access_token"]
        
        response2 = client.post(
            "/auth/token",
            data={"username": "bob@example.com", "password": "bobpass123"}
        )
        token2 = response2.json()["access_token"]
        
        return token1, token2
    
    def test_users_can_access_own_profile(self, client: TestClient):
        alice_token, bob_token = self.setup_two_users(client)
        
        alice_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        assert alice_response.status_code == 200
        alice_data = alice_response.json()
        assert alice_data["email"] == "alice@example.com"
        assert alice_data["email"] == "alice@example.com"
        assert alice_data["full_name"] == "Alice Smith"
        
        bob_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {bob_token}"}
        )
        assert bob_response.status_code == 200
        bob_data = bob_response.json()
        assert bob_data["email"] == "bob@example.com"
        assert bob_data["email"] == "bob@example.com"
        assert bob_data["full_name"] == "Bob Jones"
    
    def test_users_cannot_access_without_token(self, client: TestClient):
        response = client.get("/users/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    
    def test_users_cannot_access_with_invalid_token(self, client: TestClient):
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_users_can_update_own_profile(self, client: TestClient):
        alice_token, bob_token = self.setup_two_users(client)
        
        # Update only full name (changing email would invalidate the token)
        alice_update = {
            "full_name": "Alice Johnson"
        }
        response = client.put(
            "/users/me",
            json=alice_update,
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Alice Johnson"
        assert data["email"] == "alice@example.com"  # Email unchanged

        alice_profile = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        assert alice_profile.json()["full_name"] == "Alice Johnson"
        assert alice_profile.json()["email"] == "alice@example.com"
        
        bob_profile = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {bob_token}"}
        )
        assert bob_profile.json()["full_name"] == "Bob Jones"
    
    def test_user_tokens_are_unique(self, client: TestClient):
        alice_token, bob_token = self.setup_two_users(client)
        
        assert alice_token != bob_token
        
        alice_with_bob_token = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {bob_token}"}
        )
        assert alice_with_bob_token.status_code == 200
        assert alice_with_bob_token.json()["email"] == "bob@example.com"
        
        bob_with_alice_token = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        assert bob_with_alice_token.status_code == 200
        assert bob_with_alice_token.json()["email"] == "alice@example.com"
    
    def test_regular_users_cannot_list_all_users(self, client: TestClient):
        alice_token, _ = self.setup_two_users(client)
        
        response = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_email_update_conflict(self, client: TestClient):
        alice_token, bob_token = self.setup_two_users(client)
        
        response = client.put(
            "/users/me",
            json={"email": "bob@example.com"},
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]