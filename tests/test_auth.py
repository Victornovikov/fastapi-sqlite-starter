import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_register_user(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser1",
            "email": "test1@example.com",
            "password": "password123",
            "full_name": "Test User One"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser1"
    assert data["email"] == "test1@example.com"
    assert data["full_name"] == "Test User One"
    assert "hashed_password" not in data


def test_register_duplicate_username(client: TestClient):
    user_data = {
        "username": "duplicate",
        "email": "first@example.com",
        "password": "password123",
        "full_name": "First User"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    user_data["email"] = "second@example.com"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_register_duplicate_email(client: TestClient):
    user_data = {
        "username": "user1",
        "email": "duplicate@example.com",
        "password": "password123",
        "full_name": "First User"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    user_data["username"] = "user2"
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login_success(client: TestClient):
    client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User"
        }
    )
    
    response = client.post(
        "/auth/token",
        data={
            "username": "loginuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    client.post(
        "/auth/register",
        json={
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "correct123",
            "full_name": "Wrong Pass User"
        }
    )
    
    response = client.post(
        "/auth/token",
        data={
            "username": "wrongpass",
            "password": "wrong123"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/auth/token",
        data={
            "username": "nonexistent",
            "password": "password123"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]