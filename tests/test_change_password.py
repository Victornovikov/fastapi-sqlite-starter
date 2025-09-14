"""Tests for the change password functionality."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import User
from app.login_manager import get_password_hash, verify_password


def test_change_password_success(client: TestClient, session: Session):
    """Test successful password change."""
    # Create a test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("oldpassword123")
    )
    session.add(user)
    session.commit()

    # Login first
    login_response = client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "oldpassword123"
    })
    assert login_response.status_code == 200

    # Get profile page to get CSRF token
    profile_response = client.get("/profile")
    assert profile_response.status_code == 200

    # Extract CSRF token from cookies
    csrf_token = client.cookies.get("csrftoken")

    # Change password
    response = client.post("/auth/change-password", data={
        "current_password": "oldpassword123",
        "new_password": "newpassword456",
        "confirm_password": "newpassword456",
        "csrf": csrf_token
    })

    assert response.status_code == 200
    assert "Password changed successfully" in response.text

    # Verify password was actually changed in database
    session.refresh(user)
    assert verify_password("newpassword456", user.hashed_password)
    assert not verify_password("oldpassword123", user.hashed_password)


def test_change_password_wrong_current(client: TestClient, session: Session):
    """Test password change with incorrect current password."""
    # Create a test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("correctpassword")
    )
    session.add(user)
    session.commit()

    # Login
    client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "correctpassword"
    })

    # Get CSRF token
    profile_response = client.get("/profile")
    csrf_token = client.cookies.get("csrftoken")

    # Try to change password with wrong current password
    response = client.post("/auth/change-password", data={
        "current_password": "wrongpassword",
        "new_password": "newpassword456",
        "confirm_password": "newpassword456",
        "csrf": csrf_token
    })

    assert response.status_code == 200
    assert "Current password is incorrect" in response.text


def test_change_password_mismatch(client: TestClient, session: Session):
    """Test password change with mismatched new passwords."""
    # Create a test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("oldpassword123")
    )
    session.add(user)
    session.commit()

    # Login
    client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "oldpassword123"
    })

    # Get CSRF token
    profile_response = client.get("/profile")
    csrf_token = client.cookies.get("csrftoken")

    # Try to change password with mismatched passwords
    response = client.post("/auth/change-password", data={
        "current_password": "oldpassword123",
        "new_password": "newpassword456",
        "confirm_password": "differentpassword",
        "csrf": csrf_token
    })

    assert response.status_code == 200
    assert "New passwords do not match" in response.text


def test_change_password_too_short(client: TestClient, session: Session):
    """Test password change with password that's too short."""
    # Create a test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("oldpassword123")
    )
    session.add(user)
    session.commit()

    # Login
    client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "oldpassword123"
    })

    # Get CSRF token
    profile_response = client.get("/profile")
    csrf_token = client.cookies.get("csrftoken")

    # Try to change to a short password
    response = client.post("/auth/change-password", data={
        "current_password": "oldpassword123",
        "new_password": "short",
        "confirm_password": "short",
        "csrf": csrf_token
    })

    assert response.status_code == 200
    assert "at least 8 characters" in response.text


def test_change_password_same_as_current(client: TestClient, session: Session):
    """Test password change with same password as current."""
    # Create a test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("samepassword123")
    )
    session.add(user)
    session.commit()

    # Login
    client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "samepassword123"
    })

    # Get CSRF token
    profile_response = client.get("/profile")
    csrf_token = client.cookies.get("csrftoken")

    # Try to change to the same password
    response = client.post("/auth/change-password", data={
        "current_password": "samepassword123",
        "new_password": "samepassword123",
        "confirm_password": "samepassword123",
        "csrf": csrf_token
    })

    assert response.status_code == 200
    assert "must be different from current password" in response.text


def test_change_password_not_authenticated(client: TestClient):
    """Test password change without authentication."""
    # Try to change password without being logged in
    response = client.post("/auth/change-password", data={
        "current_password": "oldpassword",
        "new_password": "newpassword",
        "confirm_password": "newpassword",
        "csrf": "sometoken"
    })

    # Should get 401 Unauthorized
    assert response.status_code == 401


def test_change_password_invalid_csrf(client: TestClient, session: Session):
    """Test password change with invalid CSRF token."""
    # Create a test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("password123")
    )
    session.add(user)
    session.commit()

    # Login
    client.post("/auth/token", data={
        "username": "test@example.com",
        "password": "password123"
    })

    # Try to change password with invalid CSRF
    response = client.post("/auth/change-password", data={
        "current_password": "password123",
        "new_password": "newpassword456",
        "confirm_password": "newpassword456",
        "csrf": "invalid_token"
    })

    assert response.status_code == 200
    assert "Security validation failed" in response.text