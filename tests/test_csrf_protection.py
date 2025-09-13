import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import User
from app.login_manager import get_password_hash
from app.security import generate_csrf_token


class TestCSRFProtection:
    """Test CSRF protection on UI endpoints"""

    def test_login_page_sets_csrf_cookie(self, client: TestClient):
        """Test that login page sets CSRF cookie and includes token in template"""
        response = client.get("/login")
        assert response.status_code == 200

        # Check that CSRF cookie is set
        assert "csrftoken" in response.cookies

        # Check that CSRF token is in the response (would be in form)
        assert 'name="csrf"' in response.text

    def test_login_requires_csrf_token(self, client: TestClient, session: Session):
        """Test that login POST requires valid CSRF token"""
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Test User"
        )
        session.add(user)
        session.commit()

        # Try to login without CSRF token
        response = client.post(
            "/auth/login",
            data={
                "email": "test@example.com",
                "password": "testpass"
            }
        )
        # Should fail with 422 (missing required field)
        assert response.status_code == 422

        # Try with invalid CSRF token
        client.cookies.set("csrftoken", "valid_token")
        response = client.post(
            "/auth/login",
            data={
                "email": "test@example.com",
                "password": "testpass",
                "csrf": "invalid_token"
            }
        )
        # Should fail with 403 (CSRF verification failed)
        assert response.status_code == 403
        assert "CSRF verification failed" in response.json()["detail"]

    def test_login_with_valid_csrf_token(self, client: TestClient, session: Session):
        """Test that login works with valid CSRF token"""
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Test User"
        )
        session.add(user)
        session.commit()

        # Get login page to get CSRF token
        response = client.get("/login")
        csrf_token = response.cookies.get("csrftoken")

        # Login with valid CSRF token (without HX-Request header, so gets standard redirect)
        response = client.post(
            "/auth/login",
            data={
                "email": "test@example.com",
                "password": "testpass",
                "csrf": csrf_token
            },
            cookies={"csrftoken": csrf_token},
            follow_redirects=False
        )

        # Should succeed with standard redirect (303) and cookie
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"
        assert "access-token" in response.cookies

    def test_signup_requires_csrf_token(self, client: TestClient):
        """Test that signup POST requires valid CSRF token"""
        # Try to signup without CSRF token
        response = client.post(
            "/auth/signup",
            data={
                "email": "new@example.com",
                "full_name": "New User",
                "password": "newpass"
            }
        )
        # Should fail with 422 (missing required field)
        assert response.status_code == 422

        # Try with invalid CSRF token
        client.cookies.set("csrftoken", "valid_token")
        response = client.post(
            "/auth/signup",
            data={
                "email": "new@example.com",
                "full_name": "New User",
                "password": "newpass",
                "csrf": "invalid_token"
            }
        )
        # Should fail with 403 (CSRF verification failed)
        assert response.status_code == 403

    def test_signup_with_valid_csrf_token(self, client: TestClient):
        """Test that signup works with valid CSRF token"""
        # Get login page to get CSRF token
        response = client.get("/login")
        csrf_token = response.cookies.get("csrftoken")

        # Signup with valid CSRF token (without HX-Request header, so gets standard redirect)
        response = client.post(
            "/auth/signup",
            data={
                "email": "new@example.com",
                "full_name": "New User",
                "password": "newpass",
                "csrf": csrf_token
            },
            cookies={"csrftoken": csrf_token},
            follow_redirects=False
        )

        # Should succeed with standard redirect (303) and cookie
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"
        assert "access-token" in response.cookies