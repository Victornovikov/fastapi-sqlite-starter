import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import User
from app.login_manager import get_password_hash


def test_home_page_renders(client: TestClient):
    """Test that home page renders without authentication"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_login_page_renders(client: TestClient):
    """Test that login page renders and includes CSRF token"""
    response = client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "csrf" in response.cookies
    # Check that CSRF token is in the form
    assert 'name="csrf"' in response.text


def test_login_page_redirects_when_authenticated(client: TestClient, session: Session):
    """Test that login page redirects to dashboard when already logged in"""
    # Create and login user
    user = User(
        email="loggedin@example.com",
        full_name="Logged In User",
        hashed_password=get_password_hash("loggedinpass123")
    )
    session.add(user)
    session.commit()

    # Login
    login_response = client.post(
        "/auth/token",
        data={"username": "loggedin@example.com", "password": "loggedinpass123"}
    )
    token = login_response.cookies.get("access-token")

    # Try to access login page while authenticated
    response = client.get(
        "/login",
        cookies={"access-token": token},
        follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_dashboard_requires_authentication(client: TestClient):
    """Test that dashboard redirects to login when not authenticated"""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_dashboard_renders_for_authenticated_user(client: TestClient, session: Session):
    """Test that dashboard renders for authenticated users"""
    # Create and login user
    user = User(
        email="dashboard@example.com",
        full_name="Dashboard User",
        hashed_password=get_password_hash("dashpass123")
    )
    session.add(user)
    session.commit()

    # Login
    login_response = client.post(
        "/auth/token",
        data={"username": "dashboard@example.com", "password": "dashpass123"}
    )
    token = login_response.cookies.get("access-token")

    # Access dashboard
    response = client.get(
        "/dashboard",
        cookies={"access-token": token}
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Check user info is in the page
    assert "Dashboard User" in response.text or "dashboard@example.com" in response.text


def test_profile_requires_authentication(client: TestClient):
    """Test that profile page redirects to login when not authenticated"""
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_profile_renders_for_authenticated_user(client: TestClient, session: Session):
    """Test that profile page renders for authenticated users"""
    # Create and login user
    user = User(
        email="profile@example.com",
        full_name="Profile User",
        hashed_password=get_password_hash("profilepass123")
    )
    session.add(user)
    session.commit()

    # Login
    login_response = client.post(
        "/auth/token",
        data={"username": "profile@example.com", "password": "profilepass123"}
    )
    token = login_response.cookies.get("access-token")

    # Access profile
    response = client.get(
        "/profile",
        cookies={"access-token": token}
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Check user info is displayed
    assert "profile@example.com" in response.text
    assert "Profile User" in response.text


def test_htmx_login_returns_redirect_header(client: TestClient, session: Session):
    """Test that HTMX login requests get HX-Redirect header"""
    # Create user
    user = User(
        email="htmx@example.com",
        full_name="HTMX User",
        hashed_password=get_password_hash("htmxpass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Login with HTMX header
    response = client.post(
        "/auth/login",
        data={
            "email": "htmx@example.com",
            "password": "htmxpass123",
            "csrf": csrf_token
        },
        headers={
            "Cookie": f"csrf={csrf_token}",
            "HX-Request": "true"
        }
    )

    assert response.status_code == 204  # No content
    assert response.headers.get("HX-Redirect") == "/dashboard"


def test_non_htmx_login_returns_standard_redirect(client: TestClient, session: Session):
    """Test that non-HTMX login requests get standard redirect"""
    # Create user
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

    # Login without HTMX header
    response = client.post(
        "/auth/login",
        data={
            "email": "standard@example.com",
            "password": "standardpass123",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"},
        follow_redirects=False
    )

    assert response.status_code == 303  # See other
    assert response.headers.get("location") == "/dashboard"


def test_htmx_signup_returns_redirect_header(client: TestClient):
    """Test that HTMX signup requests get HX-Redirect header"""
    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Signup with HTMX header
    response = client.post(
        "/auth/signup",
        data={
            "email": "htmxsignup@example.com",
            "password": "htmxsignuppass123",
            "full_name": "HTMX Signup User",
            "csrf": csrf_token
        },
        headers={
            "Cookie": f"csrf={csrf_token}",
            "HX-Request": "true"
        }
    )

    assert response.status_code == 204  # No content
    assert response.headers.get("HX-Redirect") == "/dashboard"
    assert "access-token" in response.cookies


def test_web_login_error_returns_fragment(client: TestClient, session: Session):
    """Test that login errors return HTML fragment for HTMX"""
    # Create user
    user = User(
        email="error@example.com",
        full_name="Error User",
        hashed_password=get_password_hash("correctpass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Login with wrong password
    response = client.post(
        "/auth/login",
        data={
            "email": "error@example.com",
            "password": "wrongpass123",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 200  # Returns HTML fragment
    assert "Invalid email or password" in response.text
    assert "text/html" in response.headers["content-type"]
    # Should be a fragment, not a full page
    assert "<!DOCTYPE" not in response.text


def test_web_signup_error_returns_fragment(client: TestClient, session: Session):
    """Test that signup errors return HTML fragment for HTMX"""
    # Create existing user
    user = User(
        email="existing@example.com",
        full_name="Existing User",
        hashed_password=get_password_hash("existingpass123")
    )
    session.add(user)
    session.commit()

    # Get CSRF token
    login_page = client.get("/login")
    csrf_token = login_page.cookies.get("csrf")

    # Try to signup with existing email
    response = client.post(
        "/auth/signup",
        data={
            "email": "existing@example.com",
            "password": "newpass123",
            "full_name": "New User",
            "csrf": csrf_token
        },
        headers={"Cookie": f"csrf={csrf_token}"}
    )

    assert response.status_code == 200  # Returns HTML fragment
    assert "Email already registered" in response.text
    assert "text/html" in response.headers["content-type"]
    # Should be a fragment, not a full page
    assert "<!DOCTYPE" not in response.text


def test_forgot_password_page_renders(client: TestClient):
    """Test that forgot password page renders"""
    response = client.get("/forgot")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "csrf" in response.cookies


def test_forgot_password_redirects_when_authenticated(client: TestClient, session: Session):
    """Test that forgot password redirects when already logged in"""
    # Create and login user
    user = User(
        email="forgot@example.com",
        full_name="Forgot User",
        hashed_password=get_password_hash("forgotpass123")
    )
    session.add(user)
    session.commit()

    # Login
    login_response = client.post(
        "/auth/token",
        data={"username": "forgot@example.com", "password": "forgotpass123"}
    )
    token = login_response.cookies.get("access-token")

    # Try to access forgot page while authenticated
    response = client.get(
        "/forgot",
        cookies={"access-token": token},
        follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_logout_redirects_to_home(client: TestClient, session: Session):
    """Test that logout redirects to home page"""
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
    token = login_response.cookies.get("access-token")

    # Logout
    response = client.post(
        "/logout",
        cookies={"access-token": token},
        follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/"