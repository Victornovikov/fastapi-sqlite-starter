import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestUserAccessControl:

    def test_users_can_access_own_profile(self, client: TestClient):
        # Each user should have their own client to simulate separate browser sessions
        from fastapi.testclient import TestClient
        alice_client = TestClient(client.app)
        bob_client = TestClient(client.app)

        # Register users
        alice_data = {
            "email": "alice@example.com",
            "password": "alicepass123",
            "full_name": "Alice Smith"
        }
        bob_data = {
            "email": "bob@example.com",
            "password": "bobpass123",
            "full_name": "Bob Jones"
        }

        client.post("/auth/register", json=alice_data)
        client.post("/auth/register", json=bob_data)

        # Login with separate clients (simulating different browser sessions)
        alice_client.post(
            "/auth/token",
            data={"username": "alice@example.com", "password": "alicepass123"}
        )
        bob_client.post(
            "/auth/token",
            data={"username": "bob@example.com", "password": "bobpass123"}
        )

        # Each client now has their own cookie
        alice_response = alice_client.get("/users/me")
        assert alice_response.status_code == 200
        alice_data = alice_response.json()
        assert alice_data["email"] == "alice@example.com"
        assert alice_data["full_name"] == "Alice Smith"

        bob_response = bob_client.get("/users/me")
        assert bob_response.status_code == 200
        bob_data = bob_response.json()
        assert bob_data["email"] == "bob@example.com"
        assert bob_data["full_name"] == "Bob Jones"
    
    def test_users_cannot_access_without_token(self, client: TestClient):
        response = client.get("/users/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"
    
    def test_users_cannot_access_with_invalid_token(self, client: TestClient):
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_users_can_update_own_profile(self, client: TestClient):
        from fastapi.testclient import TestClient
        alice_client = TestClient(client.app)
        bob_client = TestClient(client.app)

        # Register users
        alice_data = {
            "email": "alice@example.com",
            "password": "alicepass123",
            "full_name": "Alice Smith"
        }
        bob_data = {
            "email": "bob@example.com",
            "password": "bobpass123",
            "full_name": "Bob Jones"
        }

        client.post("/auth/register", json=alice_data)
        client.post("/auth/register", json=bob_data)

        # Login with separate clients
        alice_client.post(
            "/auth/token",
            data={"username": "alice@example.com", "password": "alicepass123"}
        )
        bob_client.post(
            "/auth/token",
            data={"username": "bob@example.com", "password": "bobpass123"}
        )

        # Update only full name (changing email would invalidate the token)
        alice_update = {
            "full_name": "Alice Johnson"
        }
        response = alice_client.put(
            "/users/me",
            json=alice_update
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Alice Johnson"
        assert data["email"] == "alice@example.com"  # Email unchanged

        alice_profile = alice_client.get("/users/me")
        assert alice_profile.json()["full_name"] == "Alice Johnson"
        assert alice_profile.json()["email"] == "alice@example.com"

        bob_profile = bob_client.get("/users/me")
        assert bob_profile.json()["full_name"] == "Bob Jones"
    
    def test_user_tokens_are_unique(self, client: TestClient):
        from fastapi.testclient import TestClient
        alice_client = TestClient(client.app)
        bob_client = TestClient(client.app)

        # Register users
        alice_data = {
            "email": "alice@example.com",
            "password": "alicepass123",
            "full_name": "Alice Smith"
        }
        bob_data = {
            "email": "bob@example.com",
            "password": "bobpass123",
            "full_name": "Bob Jones"
        }

        client.post("/auth/register", json=alice_data)
        client.post("/auth/register", json=bob_data)

        # Login and get tokens
        alice_resp = alice_client.post(
            "/auth/token",
            data={"username": "alice@example.com", "password": "alicepass123"}
        )
        alice_token = alice_resp.json()["access_token"]

        bob_resp = bob_client.post(
            "/auth/token",
            data={"username": "bob@example.com", "password": "bobpass123"}
        )
        bob_token = bob_resp.json()["access_token"]

        assert alice_token != bob_token

        # Use a fresh client to test cross-token access
        fresh_client = TestClient(client.app)

        # Test that Bob's token returns Bob's data
        bob_token_response = fresh_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {bob_token}"}
        )
        assert bob_token_response.status_code == 200
        assert bob_token_response.json()["email"] == "bob@example.com"

        # Test that Alice's token returns Alice's data
        alice_token_response = fresh_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {alice_token}"}
        )
        assert alice_token_response.status_code == 200
        assert alice_token_response.json()["email"] == "alice@example.com"
    
    def test_regular_users_cannot_list_all_users(self, client: TestClient):
        from fastapi.testclient import TestClient
        alice_client = TestClient(client.app)

        # Register and login Alice
        alice_data = {
            "email": "alice@example.com",
            "password": "alicepass123",
            "full_name": "Alice Smith"
        }

        client.post("/auth/register", json=alice_data)
        alice_client.post(
            "/auth/token",
            data={"username": "alice@example.com", "password": "alicepass123"}
        )

        # Try to access user list (should fail - not admin)
        response = alice_client.get("/users/")
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_email_update_conflict(self, client: TestClient):
        from fastapi.testclient import TestClient
        alice_client = TestClient(client.app)

        # Register users
        alice_data = {
            "email": "alice@example.com",
            "password": "alicepass123",
            "full_name": "Alice Smith"
        }
        bob_data = {
            "email": "bob@example.com",
            "password": "bobpass123",
            "full_name": "Bob Jones"
        }

        client.post("/auth/register", json=alice_data)
        client.post("/auth/register", json=bob_data)

        # Login Alice
        alice_client.post(
            "/auth/token",
            data={"username": "alice@example.com", "password": "alicepass123"}
        )

        # Try to update Alice's email to Bob's (should fail)
        response = alice_client.put(
            "/users/me",
            json={"email": "bob@example.com"}
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]