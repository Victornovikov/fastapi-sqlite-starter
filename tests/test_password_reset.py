"""
Comprehensive password reset testing - combines unit and integration tests
"""
import pytest
import secrets
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import User, PasswordResetToken
from app.security import sha256_hex
from app.login_manager import get_password_hash, verify_password


class TestPasswordReset:
    """Complete password reset functionality tests"""

    def test_forgot_password_page_renders(self, client: TestClient):
        """Test that forgot password page loads correctly"""
        response = client.get("/forgot")
        assert response.status_code == 200
        assert "Reset Password" in response.text
        assert "Enter your email" in response.text

    def test_forgot_password_creates_token(self, client: TestClient, session: Session):
        """Test that requesting password reset creates a valid token"""
        # Create a user
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("oldpassword")
        )
        session.add(user)
        session.commit()

        # Get CSRF token
        response = client.get("/forgot")
        csrf_token = response.cookies.get("csrftoken")

        # Request password reset
        response = client.post(
            "/auth/forgot",
            data={"email": "test@example.com", "csrf": csrf_token},
            headers={"Cookie": f"csrftoken={csrf_token}"}
        )
        assert response.status_code == 200
        assert "If an account exists" in response.text

        # Check that a token was created
        reset_token = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        ).first()
        assert reset_token is not None
        assert reset_token.used_at is None
        # SQLite stores datetime without timezone, so compare as naive
        assert reset_token.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)

    def test_forgot_password_no_user_no_reveal(self, client: TestClient, session: Session):
        """Test that forgot password doesn't reveal if user doesn't exist"""
        # Get CSRF token
        response = client.get("/forgot")
        csrf_token = response.cookies.get("csrftoken")

        # Request reset for non-existent user
        response = client.post(
            "/auth/forgot",
            data={"email": "nonexistent@example.com", "csrf": csrf_token},
            headers={"Cookie": f"csrftoken={csrf_token}"}
        )

        # Should return same message to not reveal user existence
        assert response.status_code == 200
        assert "If an account exists" in response.text

        # No token should be created
        tokens = session.exec(select(PasswordResetToken)).all()
        assert len(tokens) == 0

    @pytest.mark.parametrize("token_status,expected_error", [
        ("expired", "expired or invalid"),
        ("used", "already been used"),
        ("invalid", "expired or invalid"),
    ])
    def test_reset_password_invalid_tokens(
        self, client: TestClient, session: Session, token_status: str, expected_error: str
    ):
        """Test password reset with various invalid token states"""
        # Create user
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("oldpassword")
        )
        session.add(user)
        session.commit()

        # Create token based on status
        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=sha256_hex(raw_token),
            expires_at=(
                datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
                if token_status == "expired"
                else datetime.now(timezone.utc) + timedelta(hours=1)
            ),
            used_at=datetime.now(timezone.utc) if token_status == "used" else None
        )
        session.add(reset_token)
        session.commit()

        # Use invalid token for "invalid" status
        if token_status == "invalid":
            raw_token = "completely-invalid-token"

        # Try to use the token
        response = client.get(f"/reset?token={raw_token}")

        if token_status == "invalid":
            # Invalid token shows error page
            assert response.status_code == 200
            assert expected_error in response.text.lower()
        else:
            # Expired/used tokens show the form but will fail on submit
            response = client.get(f"/reset?token={raw_token}")
            csrf_token = response.cookies.get("csrftoken")

            response = client.post(
                "/auth/reset",
                data={
                    "token": raw_token,
                    "password": "newpassword123",
                    "password_confirm": "newpassword123",
                    "csrf": csrf_token
                },
                headers={"Cookie": f"csrftoken={csrf_token}"}
            )
            assert expected_error in response.text.lower()

    def test_password_reset_complete_flow(self, client: TestClient, session: Session):
        """Test the complete password reset flow from request to completion"""
        # Step 1: Create and register a user
        user_data = {
            "email": "resetuser@example.com",
            "password": "oldpassword123",
            "full_name": "Reset Test User"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200

        test_user = session.exec(
            select(User).where(User.email == "resetuser@example.com")
        ).first()

        # Step 2: Request password reset
        response = client.get("/forgot")
        csrf_token = response.cookies.get("csrftoken")

        response = client.post(
            "/auth/forgot",
            data={"email": "resetuser@example.com", "csrf": csrf_token},
            headers={"Cookie": f"csrftoken={csrf_token}"}
        )
        assert response.status_code == 200

        # Step 3: Get the token from database (simulating email link)
        reset_token_record = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id)
        ).first()
        assert reset_token_record is not None

        # Generate a valid token for testing (in real scenario, this would be from email)
        raw_token = secrets.token_urlsafe(32)
        reset_token_record.token_hash = sha256_hex(raw_token)
        session.add(reset_token_record)
        session.commit()

        # Step 4: Visit reset page with token
        response = client.get(f"/reset?token={raw_token}")
        assert response.status_code == 200
        csrf_token = response.cookies.get("csrftoken")

        # Step 5: Submit new password
        response = client.post(
            "/auth/reset",
            data={
                "token": raw_token,
                "password": "newpassword123",
                "password_confirm": "newpassword123",
                "csrf": csrf_token
            },
            headers={"Cookie": f"csrftoken={csrf_token}"}
        )

        # Should redirect to login
        assert response.status_code in [204, 303]  # HTMX redirect or regular redirect

        # Step 6: Verify password was changed
        session.refresh(test_user)
        assert verify_password("newpassword123", test_user.hashed_password) is True
        assert verify_password("oldpassword123", test_user.hashed_password) is False

        # Step 7: Verify token was marked as used
        session.refresh(reset_token_record)
        assert reset_token_record.used_at is not None

        # Step 8: Verify can login with new password
        response = client.post(
            "/auth/token",
            data={"username": "resetuser@example.com", "password": "newpassword123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()