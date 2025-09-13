import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_register_user(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "email": "test1@example.com",
            "password": "password123",
            "full_name": "Test User One"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test1@example.com"
    assert data["full_name"] == "Test User One"
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient):
    user_data = {
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "First User"
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200

    # Try to register with same email
    user_data["full_name"] = "Second User"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login_success(client: TestClient):
    # First register a user
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User"
        }
    )

    # Then try to login (OAuth2 uses 'username' field but we pass email)
    response = client.post(
        "/auth/token",
        data={
            "username": "login@example.com",  # OAuth2 field name, but contains email
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    # First register a user
    client.post(
        "/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "correct123",
            "full_name": "Wrong Pass User"
        }
    )

    # Try to login with wrong password
    response = client.post(
        "/auth/token",
        data={
            "username": "wrong@example.com",  # OAuth2 field name, but contains email
            "password": "wrong123"
        }
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/auth/token",
        data={
            "username": "nonexistent@example.com",  # OAuth2 field name, but contains email
            "password": "password123"
        }
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]