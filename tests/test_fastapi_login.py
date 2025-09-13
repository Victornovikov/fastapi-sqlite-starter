import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta
import jwt
from app.models import User
from app.config import get_settings
from app.login_manager import manager, get_password_hash

settings = get_settings()


def test_login_manager_configuration():
    """Test that LoginManager is properly configured"""
    assert manager.secret == settings.secret_key
    assert manager.token_url == "/auth/token"
    assert manager.use_cookie == True
    assert manager.use_header == True
    assert manager.cookie_name == "access-token"
    assert manager.default_expiry == timedelta(minutes=settings.access_token_expire_minutes)


def test_api_login_creates_cookie(client: TestClient, session: Session):
    """Test that API login endpoint sets cookie correctly"""
    # Create test user
    user = User(
        email="cookie@example.com",
        full_name="Cookie User",
        hashed_password=get_password_hash("testpass123")
    )
    session.add(user)
    session.commit()

    # Login via API
    response = client.post(
        "/auth/token",
        data={"username": "cookie@example.com", "password": "testpass123"}
    )

    assert response.status_code == 200
    assert "access-token" in response.cookies

    # Verify cookie properties
    cookie = response.cookies.get("access-token")
    assert cookie is not None

    # Decode JWT to verify contents
    payload = jwt.decode(cookie, settings.secret_key, algorithms=["HS256"])
    assert payload["sub"] == "cookie@example.com"


def test_web_login_creates_cookie(client: TestClient, session: Session):
    """Test that web login endpoint sets cookie correctly"""
    # Create test user
    user = User(
        email="weblogin@example.com",
        full_name="Web User",
        hashed_password=get_password_hash("webpass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Login via web form
    response = client.post(
        "/auth/login",
        data={
            "email": "weblogin@example.com",
            "password": "webpass123",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 204  # HTMX redirect
    assert response.headers.get("HX-Redirect") == "/dashboard"
    assert "access-token" in response.cookies

    # Verify JWT in cookie
    cookie = response.cookies.get("access-token")
    payload = jwt.decode(cookie, settings.secret_key, algorithms=["HS256"])
    assert payload["sub"] == "weblogin@example.com"


def test_cookie_authentication_works(client: TestClient, session: Session):
    """Test that cookie-based authentication allows access to protected routes"""
    # Create and login user
    user = User(
        email="cookieauth@example.com",
        full_name="Cookie Auth User",
        hashed_password=get_password_hash("authpass123")
    )
    session.add(user)
    session.commit()

    # Login to get cookie
    login_response = client.post(
        "/auth/token",
        data={"username": "cookieauth@example.com", "password": "authpass123"}
    )

    access_token = login_response.cookies.get("access-token")

    # Access protected endpoint with cookie
    response = client.get(
        "/users/me",
        cookies={"access-token": access_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "cookieauth@example.com"
    assert data["full_name"] == "Cookie Auth User"


def test_header_authentication_works(client: TestClient, session: Session):
    """Test that header-based authentication still works for API clients"""
    # Create and login user
    user = User(
        email="headerauth@example.com",
        full_name="Header Auth User",
        hashed_password=get_password_hash("headerpass123")
    )
    session.add(user)
    session.commit()

    # Login to get token
    login_response = client.post(
        "/auth/token",
        data={"username": "headerauth@example.com", "password": "headerpass123"}
    )

    token = login_response.json()["access_token"]

    # Access protected endpoint with header
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "headerauth@example.com"


def test_logout_clears_cookie(client: TestClient, session: Session):
    """Test that logout properly clears the authentication cookie"""
    # Create and login user
    user = User(
        email="logout@example.com",
        full_name="Logout User",
        hashed_password=get_password_hash("logoutpass123")
    )
    session.add(user)
    session.commit()

    # Login
    login_response = client.post(
        "/auth/token",
        data={"username": "logout@example.com", "password": "logoutpass123"}
    )

    access_token = login_response.cookies.get("access-token")

    # Logout
    logout_response = client.post(
        "/logout",
        cookies={"access-token": access_token}
    )

    assert logout_response.status_code == 302  # Redirect to home

    # Check cookie is deleted (max-age=0 or expires in past)
    if "access-token" in logout_response.cookies:
        # Cookie should be set to expire
        cookie_header = logout_response.headers.get("set-cookie", "")
        assert "Max-Age=0" in cookie_header or "expires" in cookie_header.lower()


def test_invalid_token_rejected(client: TestClient):
    """Test that invalid tokens are properly rejected"""
    # Try with invalid token
    response = client.get(
        "/users/me",
        cookies={"access-token": "invalid.token.here"}
    )

    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]


def test_expired_token_rejected(client: TestClient, session: Session):
    """Test that expired tokens are properly rejected"""
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
        expires=timedelta(seconds=-1)  # Already expired
    )

    # Try to use expired token
    response = client.get(
        "/users/me",
        cookies={"access-token": expired_token}
    )

    assert response.status_code == 401


def test_login_with_wrong_password(client: TestClient, session: Session):
    """Test that login fails with wrong password"""
    # Create user
    user = User(
        email="wrongpass@example.com",
        full_name="Wrong Pass User",
        hashed_password=get_password_hash("correctpass123")
    )
    session.add(user)
    session.commit()

    # Try to login with wrong password
    response = client.post(
        "/auth/token",
        data={"username": "wrongpass@example.com", "password": "wrongpass123"}
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
    assert "access-token" not in response.cookies


def test_login_with_nonexistent_user(client: TestClient):
    """Test that login fails for non-existent user"""
    response = client.post(
        "/auth/token",
        data={"username": "nonexistent@example.com", "password": "anypass123"}
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
    assert "access-token" not in response.cookies


def test_inactive_user_cannot_login(client: TestClient, session: Session):
    """Test that inactive users cannot login"""
    # Create inactive user
    user = User(
        email="inactive@example.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("inactivepass123"),
        is_active=False
    )
    session.add(user)
    session.commit()

    # Try to login
    response = client.post(
        "/auth/token",
        data={"username": "inactive@example.com", "password": "inactivepass123"}
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_protected_route_without_auth(client: TestClient):
    """Test that protected routes require authentication"""
    # Try to access protected route without auth
    response = client.get("/users/me")

    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]


def test_optional_auth_route_without_auth(client: TestClient):
    """Test that optional auth routes work without authentication"""
    response = client.get("/")

    assert response.status_code == 200
    # Should render page without user context


def test_optional_auth_route_with_auth(client: TestClient, session: Session):
    """Test that optional auth routes work with authentication"""
    # Create and login user
    user = User(
        email="optional@example.com",
        full_name="Optional User",
        hashed_password=get_password_hash("optionalpass123")
    )
    session.add(user)
    session.commit()

    # Login
    login_response = client.post(
        "/auth/token",
        data={"username": "optional@example.com", "password": "optionalpass123"}
    )

    access_token = login_response.cookies.get("access-token")

    # Access optional auth route
    response = client.get(
        "/",
        cookies={"access-token": access_token}
    )

    assert response.status_code == 200
    # Page should include user context
    assert "optional@example.com" in response.text or "Optional User" in response.text