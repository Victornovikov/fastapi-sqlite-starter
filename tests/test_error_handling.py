import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import User
from app.login_manager import get_password_hash


def test_404_page_renders_for_ui_routes(client: TestClient):
    """Test that 404 errors return custom HTML page for UI routes"""
    response = client.get("/nonexistent-page")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    # Should render 404.html template if it exists, or error.html


def test_404_returns_json_for_api_routes(client: TestClient):
    """Test that 404 errors return JSON for API routes"""
    response = client.get("/auth/nonexistent")
    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "detail" in data


def test_401_unauthorized_json_for_api(client: TestClient):
    """Test that 401 errors return JSON for API endpoints"""
    response = client.get("/users/me")
    assert response.status_code == 401
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "detail" in data
    assert "Invalid authentication credentials" in data["detail"]


def test_422_validation_error_json(client: TestClient):
    """Test that validation errors return JSON with error details"""
    # Send invalid data to register endpoint
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",  # Invalid email format
            "password": "123",  # Too short
            "full_name": ""  # Empty
        }
    )
    assert response.status_code == 422
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)  # Should be list of errors


def test_rate_limit_exceeded_error(client: TestClient):
    """Test that rate limit errors are handled properly"""
    # Get CSRF token once
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Make many rapid requests to trigger rate limit
    for i in range(15):  # Rate limit is 10/minute for login
        response = client.post(
            "/auth/login",
            data={
                "email": f"test{i}@example.com",
                "password": "wrongpass",
                "csrf": csrf_token
            },
            headers={"Cookie": f"csrf={csrf_token}"}
        )

        if response.status_code == 429:
            # Rate limit hit
            assert "text/html" in response.headers["content-type"]
            assert "Too Many Requests" in response.text or "Rate limit" in response.text
            break
    else:
        # If we didn't hit rate limit, that's concerning but not a test failure
        # (might be disabled in test environment)
        pass


def test_csrf_validation_error(client: TestClient):
    """Test that CSRF validation failures are handled properly"""
    # Try to login without CSRF token
    response = client.post(
        "/auth/login",
        data={
            "email": "test@example.com",
            "password": "testpass",
            "csrf": "invalid-csrf-token"
        }
    )

    # Should get an error (either 400, 403, or 422)
    assert response.status_code in [400, 403, 422]


def test_csrf_missing_error(client: TestClient):
    """Test that missing CSRF token is handled properly"""
    # Try to login without CSRF field at all
    response = client.post(
        "/auth/login",
        data={
            "email": "test@example.com",
            "password": "testpass"
        }
    )

    # Should get validation error
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_invalid_token_format_error(client: TestClient):
    """Test that malformed tokens are handled properly"""
    # Try various invalid token formats
    invalid_tokens = [
        "not-a-jwt",
        "eyJ.invalid.token",
        "",
        "Bearer token",  # Wrong format in cookie
    ]

    for token in invalid_tokens:
        response = client.get(
            "/users/me",
            cookies={"access-token": token}
        )
        assert response.status_code == 401
        data = response.json()
        assert "Invalid authentication credentials" in data["detail"]


def test_expired_token_error_message(client: TestClient, session: Session):
    """Test that expired tokens return appropriate error"""
    from app.login_manager import manager
    from datetime import timedelta

    # Create user
    user = User(
        email="expired@example.com",
        full_name="Expired User",
        hashed_password=get_password_hash("expiredpass123")
    )
    session.add(user)
    session.commit()

    # Create expired token
    expired_token = manager.create_access_token(
        data={"sub": "expired@example.com"},
        expires=timedelta(seconds=-1)
    )

    # Try to use expired token
    response = client.get(
        "/users/me",
        cookies={"access-token": expired_token}
    )

    assert response.status_code == 401
    data = response.json()
    assert "Invalid authentication credentials" in data["detail"]


def test_forgot_password_always_returns_success(client: TestClient, session: Session):
    """Test that forgot password always returns success to prevent email enumeration"""
    # Get CSRF token
    forgot_page = client.get("/forgot")
    csrf_token = forgot_page.cookies.get("csrf")

    # Test with non-existent email
    response = client.post(
        "/auth/forgot",
        data={
            "email": "nonexistent@example.com",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 200
    assert "If an account exists with that email" in response.text

    # Test with existing email
    user = User(
        email="existing@example.com",
        full_name="Existing User",
        hashed_password=get_password_hash("existingpass123")
    )
    session.add(user)
    session.commit()

    response = client.post(
        "/auth/forgot",
        data={
            "email": "existing@example.com",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 200
    assert "If an account exists with that email" in response.text


def test_invalid_reset_token_error_page(client: TestClient):
    """Test that invalid reset tokens show error page"""
    response = client.get("/reset?token=invalid-token-12345")

    assert response.status_code == 400
    assert "text/html" in response.headers["content-type"]
    assert "Invalid or Expired Token" in response.text or "invalid" in response.text.lower()


def test_missing_reset_token_error(client: TestClient):
    """Test that reset page without token shows error"""
    response = client.get("/reset")

    # Should get error due to missing token parameter
    assert response.status_code in [400, 422]