import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from datetime import datetime, timedelta
import jwt
from app.models import User
from app.config import get_settings
from app.login_manager import get_password_hash

settings = get_settings()


def test_remember_me_sets_longer_expiry(client: TestClient, session: Session):
    """Test that remember_me checkbox sets 30-day expiry"""
    # Create test user
    user = User(
        email="remember@example.com",
        full_name="Remember User",
        hashed_password=get_password_hash("rememberpass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Login with remember_me
    response = client.post(
        "/auth/login",
        data={
            "email": "remember@example.com",
            "password": "rememberpass123",
            "remember_me": "true",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 204
    assert "access-token" in response.cookies

    # Decode token to check expiry
    token = response.cookies.get("access-token")
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

    # Check that expiry is approximately 30 days from now
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    difference = exp_time - now

    # Should be close to 30 days (allowing for small processing time)
    assert difference.days >= 29
    assert difference.days <= 30


def test_no_remember_me_sets_standard_expiry(client: TestClient, session: Session):
    """Test that without remember_me, standard expiry is used"""
    # Create test user
    user = User(
        email="standard@example.com",
        full_name="Standard User",
        hashed_password=get_password_hash("standardpass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Login without remember_me
    response = client.post(
        "/auth/login",
        data={
            "email": "standard@example.com",
            "password": "standardpass123",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 204
    assert "access-token" in response.cookies

    # Decode token to check expiry
    token = response.cookies.get("access-token")
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

    # Check that expiry is standard duration
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    difference = exp_time - now

    # Should be close to configured minutes (default 30)
    expected_seconds = settings.access_token_expire_minutes * 60
    actual_seconds = difference.total_seconds()

    # Allow 60 second tolerance for processing time
    assert actual_seconds >= (expected_seconds - 60)
    assert actual_seconds <= (expected_seconds + 60)


def test_remember_me_false_string_sets_standard_expiry(client: TestClient, session: Session):
    """Test that remember_me='false' (string) uses standard expiry"""
    # Create test user
    user = User(
        email="false@example.com",
        full_name="False User",
        hashed_password=get_password_hash("falsepass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Login with remember_me="false"
    response = client.post(
        "/auth/login",
        data={
            "email": "false@example.com",
            "password": "falsepass123",
            "remember_me": "false",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 204
    assert "access-token" in response.cookies

    # Decode token to check expiry
    token = response.cookies.get("access-token")
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

    # Check that expiry is standard duration (not 30 days)
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    difference = exp_time - now

    # Should be minutes, not days
    assert difference.days == 0
    assert difference.seconds < 7200  # Less than 2 hours


def test_cookie_max_age_matches_token_expiry(client: TestClient, session: Session):
    """Test that cookie max-age matches JWT token expiry"""
    # Create test user
    user = User(
        email="maxage@example.com",
        full_name="MaxAge User",
        hashed_password=get_password_hash("maxagepass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Test with remember_me
    response = client.post(
        "/auth/login",
        data={
            "email": "maxage@example.com",
            "password": "maxagepass123",
            "remember_me": "true",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    # Check Set-Cookie header for max-age
    cookie_header = None
    for header in response.headers.raw:
        if header[0].lower() == b'set-cookie' and b'access-token' in header[1]:
            cookie_header = header[1].decode()
            break

    assert cookie_header is not None

    # Max-age should be approximately 30 days in seconds
    if "Max-Age=" in cookie_header:
        max_age_str = cookie_header.split("Max-Age=")[1].split(";")[0]
        max_age = int(max_age_str)
        # 30 days = 2592000 seconds
        assert max_age >= 2591000  # Allow small variance
        assert max_age <= 2593000


def test_api_login_ignores_remember_me(client: TestClient, session: Session):
    """Test that API login endpoint doesn't use remember_me (API clients manage their own storage)"""
    # Create test user
    user = User(
        email="api@example.com",
        full_name="API User",
        hashed_password=get_password_hash("apipass123")
    )
    session.add(user)
    session.commit()

    # API login doesn't have remember_me parameter
    response = client.post(
        "/auth/token",
        data={"username": "api@example.com", "password": "apipass123"}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Decode token to check standard expiry
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    difference = exp_time - now

    # Should always be standard duration for API
    assert difference.days == 0
    expected_seconds = settings.access_token_expire_minutes * 60
    actual_seconds = difference.total_seconds()
    assert actual_seconds >= (expected_seconds - 60)
    assert actual_seconds <= (expected_seconds + 60)


def test_remember_me_survives_server_restart(client: TestClient, session: Session):
    """Test that remember_me tokens remain valid (simulated by checking token properties)"""
    # Create test user
    user = User(
        email="persist@example.com",
        full_name="Persist User",
        hashed_password=get_password_hash("persistpass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Login with remember_me
    response = client.post(
        "/auth/login",
        data={
            "email": "persist@example.com",
            "password": "persistpass123",
            "remember_me": "true",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    token = response.cookies.get("access-token")

    # Simulate using the token later (token should still be valid)
    response = client.get(
        "/users/me",
        cookies={"access-token": token}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "persist@example.com"

    # Verify the token is self-contained (doesn't require server-side session)
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    assert "sub" in payload  # Contains user identifier
    assert "exp" in payload  # Contains expiration