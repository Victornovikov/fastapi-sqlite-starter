"""
Consolidated authentication tests - combines auth.py and fastapi_login.py
"""
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import User
from app.login_manager import manager, get_password_hash


class TestRegistration:
    """User registration tests"""

    def test_register_user_success(self, client: TestClient):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient):
        """Test that duplicate email registration fails"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User"
        }

        # First registration succeeds
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200

        # Second registration with same email fails
        user_data["full_name"] = "Second User"
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]


class TestLogin:
    """Login and authentication tests"""

    @pytest.mark.parametrize("endpoint,data_format", [
        ("/auth/token", "form"),  # API endpoint
        ("/auth/login", "form_with_csrf"),  # Web endpoint
    ])
    def test_login_success_creates_cookie(
        self, client: TestClient, session: Session, endpoint: str, data_format: str
    ):
        """Test successful login creates cookie and returns token"""
        # Create user
        user = User(
            email="login@example.com",
            full_name="Login User",
            hashed_password=get_password_hash("correctpass123")
        )
        session.add(user)
        session.commit()

        # Prepare login data
        if data_format == "form":
            # API endpoint uses OAuth2 format
            login_data = {"username": "login@example.com", "password": "correctpass123"}
            headers = {}
        else:
            # Web endpoint needs CSRF
            csrf_response = client.get("/login")
            csrf_token = csrf_response.cookies.get("csrftoken")
            login_data = {
                "email": "login@example.com",
                "password": "correctpass123",
                "csrf": csrf_token
            }
            headers = {"Cookie": f"csrftoken={csrf_token}"}

        # Login
        response = client.post(endpoint, data=login_data, headers=headers, follow_redirects=False)

        if endpoint == "/auth/token":
            # API returns JSON with token
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
        else:
            # Web redirects
            assert response.status_code in [303, 204]

        # Both should set cookie
        assert "access-token" in response.cookies

    @pytest.mark.parametrize("email,password,expected_error", [
        ("wrong@example.com", "wrongpass", "Incorrect email or password"),
        ("nonexistent@example.com", "anypass", "Incorrect email or password"),
    ])
    def test_login_failures(
        self, client: TestClient, session: Session, email: str, password: str, expected_error: str
    ):
        """Test various login failure scenarios"""
        # Create user for wrong password test
        if email == "wrong@example.com":
            user = User(
                email="wrong@example.com",
                full_name="Wrong Pass User",
                hashed_password=get_password_hash("correctpass123")
            )
            session.add(user)
            session.commit()

        # Try to login
        response = client.post(
            "/auth/token",
            data={"username": email, "password": password}
        )
        assert response.status_code == 401
        assert expected_error in response.json()["detail"]

    def test_inactive_user_cannot_login(self, client: TestClient, session: Session):
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
        assert "Invalid credentials" in response.json()["detail"]


class TestTokenManagement:
    """JWT token and session management tests"""

    def test_login_manager_configuration(self):
        """Test that LoginManager is properly configured"""
        assert manager is not None
        assert manager.cookie_name == "access-token"
        assert hasattr(manager.secret, 'secret')
        # Secret should be properly configured
        secret_value = manager.secret.secret.get_secret_value() if hasattr(
            manager.secret.secret, 'get_secret_value'
        ) else manager.secret.secret
        assert len(secret_value) >= 32

    def test_cookie_authentication_works(self, client: TestClient, session: Session):
        """Test that cookie-based authentication works"""
        # Create and login user
        user = User(
            email="cookie@example.com",
            full_name="Cookie User",
            hashed_password=get_password_hash("cookiepass123")
        )
        session.add(user)
        session.commit()

        # Login
        response = client.post(
            "/auth/token",
            data={"username": "cookie@example.com", "password": "cookiepass123"}
        )
        token = response.cookies.get("access-token")

        # Use cookie to access protected endpoint
        response = client.get("/users/me", cookies={"access-token": token})
        assert response.status_code == 200
        assert response.json()["email"] == "cookie@example.com"

    def test_header_authentication_works(self, client: TestClient, session: Session):
        """Test that header-based authentication works"""
        # Create and login user
        user = User(
            email="header@example.com",
            full_name="Header User",
            hashed_password=get_password_hash("headerpass123")
        )
        session.add(user)
        session.commit()

        # Login
        response = client.post(
            "/auth/token",
            data={"username": "header@example.com", "password": "headerpass123"}
        )
        token = response.json()["access_token"]

        # Use header to access protected endpoint
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "header@example.com"

    def test_invalid_token_rejected(self, client: TestClient):
        """Test that invalid tokens are rejected"""
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_expired_token_rejected(self, client: TestClient, session: Session):
        """Test that expired tokens are rejected"""
        # Create user
        user = User(
            email="expired@example.com",
            full_name="Expired User",
            hashed_password=get_password_hash("expiredpass123")
        )
        session.add(user)
        session.commit()

        # Create expired token manually
        secret_value = manager.secret.secret.get_secret_value() if hasattr(
            manager.secret.secret, 'get_secret_value'
        ) else manager.secret.secret

        expired_token = jwt.encode(
            {
                "sub": "expired@example.com",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1)
            },
            secret_value,
            algorithm="HS256"
        )

        # Try to use expired token
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_logout_clears_cookie(self, client: TestClient, session: Session):
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
        response = client.post(
            "/auth/token",
            data={"username": "logout@example.com", "password": "logoutpass123"}
        )
        token = response.cookies.get("access-token")
        assert token is not None

        # Logout
        response = client.get("/logout", cookies={"access-token": token})

        # Cookie should be cleared
        set_cookie = response.headers.get("set-cookie", "")
        assert "access-token" in set_cookie
        assert "Max-Age=0" in set_cookie or 'max-age="0"' in set_cookie


class TestProtectedEndpoints:
    """Tests for protected endpoint access"""

    def test_protected_route_without_auth(self, client: TestClient):
        """Test that protected routes require authentication"""
        response = client.get("/users/me")
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_optional_auth_route_without_auth(self, client: TestClient):
        """Test optional auth route works without authentication"""
        # Create a test endpoint that uses optional auth
        from app.main import app
        from app.login_manager import get_current_user_optional

        @app.get("/test-optional")
        async def test_optional(user=Depends(get_current_user_optional)):
            return {"user": user.email if user else None}

        response = client.get("/test-optional")
        assert response.status_code == 200
        assert response.json()["user"] is None

    def test_optional_auth_route_with_auth(self, client: TestClient, session: Session):
        """Test optional auth route recognizes authenticated users"""
        # Create and login user
        user = User(
            email="optional@example.com",
            full_name="Optional User",
            hashed_password=get_password_hash("optionalpass123")
        )
        session.add(user)
        session.commit()

        response = client.post(
            "/auth/token",
            data={"username": "optional@example.com", "password": "optionalpass123"}
        )
        token = response.cookies.get("access-token")

        # Create test endpoint
        from app.main import app
        from app.login_manager import get_current_user_optional
        from fastapi import Depends

        @app.get("/test-optional-auth")
        async def test_optional_auth(user=Depends(get_current_user_optional)):
            return {"user": user.email if user else None}

        response = client.get("/test-optional-auth", cookies={"access-token": token})
        assert response.status_code == 200
        assert response.json()["user"] == "optional@example.com"