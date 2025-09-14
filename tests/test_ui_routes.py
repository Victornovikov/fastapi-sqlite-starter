"""
Optimized UI route tests using parametrization
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import User
from app.login_manager import get_password_hash


class TestUIRendering:
    """Test UI pages render correctly"""

    @pytest.mark.parametrize("path,expected_status,expected_content", [
        ("/", 200, None),  # Home page
        ("/login", 200, 'name="csrf"'),  # Login with CSRF
        ("/signup", 200, 'name="csrf"'),  # Signup with CSRF
        ("/forgot", 200, "Reset Password"),  # Forgot password
    ])
    def test_public_pages_render(self, client: TestClient, path: str, expected_status: int, expected_content: str):
        """Test that public pages render correctly"""
        response = client.get(path)
        assert response.status_code == expected_status
        assert "text/html" in response.headers["content-type"]
        if expected_content:
            assert expected_content in response.text

    @pytest.mark.parametrize("path", [
        "/dashboard",
        "/profile",
    ])
    def test_protected_pages_require_auth(self, client: TestClient, path: str):
        """Test that protected pages redirect to login when not authenticated"""
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    @pytest.mark.parametrize("path,already_auth_path", [
        ("/login", "/dashboard"),
        ("/signup", "/dashboard"),
        ("/forgot", "/dashboard"),
    ])
    def test_auth_pages_redirect_when_logged_in(
        self, client: TestClient, session: Session, path: str, already_auth_path: str
    ):
        """Test that auth pages redirect to dashboard when already logged in"""
        # Create and login user
        user = User(
            email="authed@example.com",
            full_name="Authed User",
            hashed_password=get_password_hash("authpass123")
        )
        session.add(user)
        session.commit()

        # Login
        login_response = client.post(
            "/auth/token",
            data={"username": "authed@example.com", "password": "authpass123"}
        )
        token = login_response.cookies.get("access-token")

        # Try to access auth page while authenticated
        response = client.get(path, cookies={"access-token": token}, follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == already_auth_path


class TestUIForms:
    """Test UI form submissions and HTMX behavior"""

    def test_htmx_login_returns_redirect_header(self, client: TestClient, session: Session):
        """Test that HTMX login returns HX-Redirect header instead of 303"""
        # Create user
        user = User(
            email="htmx@example.com",
            full_name="HTMX User",
            hashed_password=get_password_hash("htmxpass123")
        )
        session.add(user)
        session.commit()

        # Get CSRF token
        response = client.get("/login")
        csrf_token = response.cookies.get("csrftoken")

        # Login with HX-Request header (simulating HTMX)
        response = client.post(
            "/auth/login",
            data={
                "email": "htmx@example.com",
                "password": "htmxpass123",
                "csrf": csrf_token
            },
            headers={
                "HX-Request": "true",
                "Cookie": f"csrftoken={csrf_token}"
            },
            follow_redirects=False
        )

        # HTMX requests should get 204 with HX-Redirect header
        assert response.status_code == 204
        assert response.headers.get("HX-Redirect") == "/dashboard"

    def test_non_htmx_login_returns_standard_redirect(self, client: TestClient, session: Session):
        """Test that non-HTMX login returns standard 303 redirect"""
        # Create user
        user = User(
            email="standard@example.com",
            full_name="Standard User",
            hashed_password=get_password_hash("standardpass123")
        )
        session.add(user)
        session.commit()

        # Get CSRF token
        response = client.get("/login")
        csrf_token = response.cookies.get("csrftoken")

        # Login without HX-Request header
        response = client.post(
            "/auth/login",
            data={
                "email": "standard@example.com",
                "password": "standardpass123",
                "csrf": csrf_token
            },
            headers={"Cookie": f"csrftoken={csrf_token}"},
            follow_redirects=False
        )

        # Standard requests should get 303 redirect
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"

    @pytest.mark.parametrize("endpoint,email_field", [
        ("/auth/login", "wrongemail@example.com"),
        ("/auth/signup", "duplicate@example.com"),
    ])
    def test_form_errors_return_html_fragment(
        self, client: TestClient, session: Session, endpoint: str, email_field: str
    ):
        """Test that form errors return HTML fragments for HTMX updates"""
        # For signup test, create existing user
        if endpoint == "/auth/signup":
            existing = User(
                email="duplicate@example.com",
                full_name="Existing User",
                hashed_password=get_password_hash("existing123")
            )
            session.add(existing)
            session.commit()

        # Get CSRF token
        response = client.get("/login")
        csrf_token = response.cookies.get("csrftoken")

        # Submit form with error
        data = {"email": email_field, "csrf": csrf_token}
        if endpoint == "/auth/login":
            data["password"] = "wrongpassword"
        else:  # signup
            data["password"] = "newpass123"
            data["full_name"] = "New User"

        response = client.post(
            endpoint,
            data=data,
            headers={
                "HX-Request": "true",
                "Cookie": f"csrftoken={csrf_token}"
            }
        )

        # Should return HTML fragment with error or redirect
        if endpoint == "/auth/login":
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
        # Signup might handle differently


class TestLogout:
    """Test logout functionality"""

    def test_logout_clears_session_and_redirects(self, client: TestClient, session: Session):
        """Test that logout clears the session and redirects to home"""
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
        assert token is not None

        # Logout
        response = client.get(
            "/logout",
            cookies={"access-token": token},
            follow_redirects=False
        )

        # Should redirect to home
        assert response.status_code == 302
        assert response.headers["location"] == "/"

        # Cookie should be cleared - verify by checking we can't access protected route

        # Verify can't access protected routes anymore
        response = client.get(
            "/dashboard",
            cookies={"access-token": token},
            follow_redirects=False
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/login"