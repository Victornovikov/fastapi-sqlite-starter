import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import User, PasswordResetToken
from app.login_manager import get_password_hash
from app.security import sha256_hex
import secrets


class TestPasswordReset:
    """Test password reset functionality"""

    def test_forgot_password_page_renders(self, client: TestClient):
        """Test that forgot password page renders correctly"""
        response = client.get("/forgot")
        assert response.status_code == 200
        assert "Reset Your Password" in response.text
        assert 'name="csrf"' in response.text

    def test_forgot_password_creates_token(self, client: TestClient, session: Session):
        """Test that forgot password creates a reset token for existing user"""
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("oldpassword"),
            full_name="Test User"
        )
        session.add(user)
        session.commit()

        # Get CSRF token
        response = client.get("/forgot")
        csrf_token = response.cookies.get("csrftoken")

        # Request password reset
        response = client.post(
            "/auth/forgot",
            data={
                "email": "test@example.com",
                "csrf": csrf_token
            },
            cookies={"csrftoken": csrf_token}
        )

        assert response.status_code == 200
        assert "If an account exists" in response.text

        # Check that a token was created
        reset_token = session.exec(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        ).first()
        assert reset_token is not None
        assert reset_token.used_at is None
        assert reset_token.expires_at > datetime.utcnow()

    def test_forgot_password_no_user(self, client: TestClient, session: Session):
        """Test that forgot password doesn't reveal if user doesn't exist"""
        # Get CSRF token
        response = client.get("/forgot")
        csrf_token = response.cookies.get("csrftoken")

        # Request password reset for non-existent user
        response = client.post(
            "/auth/forgot",
            data={
                "email": "nonexistent@example.com",
                "csrf": csrf_token
            },
            cookies={"csrftoken": csrf_token}
        )

        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "If an account exists" in response.text

        # No token should be created
        tokens = session.exec(select(PasswordResetToken)).all()
        assert len(tokens) == 0

    def test_reset_password_with_valid_token(self, client: TestClient, session: Session):
        """Test resetting password with a valid token"""
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("oldpassword"),
            full_name="Test User"
        )
        session.add(user)
        session.commit()

        # Create a valid reset token
        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=sha256_hex(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        session.add(reset_token)
        session.commit()

        # Get the reset form
        response = client.get(f"/reset?token={raw_token}")
        assert response.status_code == 200
        assert "Set New Password" in response.text

        # Get CSRF token
        csrf_token = response.cookies.get("csrftoken")

        # Reset the password (without HX-Request header, so gets standard redirect)
        response = client.post(
            "/auth/reset",
            data={
                "token": raw_token,
                "new_password": "newpassword123",
                "csrf": csrf_token
            },
            cookies={"csrftoken": csrf_token},
            follow_redirects=False
        )

        # Should redirect to login after successful reset
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

        # Refresh user and check password was changed
        session.refresh(user)
        from app.security import verify_password
        assert verify_password("newpassword123", user.hashed_password)

        # Check token was marked as used
        session.refresh(reset_token)
        assert reset_token.used_at is not None

    def test_reset_password_with_expired_token(self, client: TestClient, session: Session):
        """Test that expired tokens don't work"""
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("oldpassword"),
            full_name="Test User"
        )
        session.add(user)
        session.commit()

        # Create an expired reset token
        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=sha256_hex(raw_token),
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        session.add(reset_token)
        session.commit()

        # Try to get the reset form
        response = client.get(f"/reset?token={raw_token}")
        assert response.status_code == 400
        assert "Invalid or Expired Token" in response.text

    def test_reset_password_with_used_token(self, client: TestClient, session: Session):
        """Test that used tokens can't be reused"""
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("oldpassword"),
            full_name="Test User"
        )
        session.add(user)
        session.commit()

        # Create a used reset token
        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=sha256_hex(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used_at=datetime.utcnow()  # Already used
        )
        session.add(reset_token)
        session.commit()

        # Try to get the reset form
        response = client.get(f"/reset?token={raw_token}")
        assert response.status_code == 400
        assert "Invalid or Expired Token" in response.text

    def test_reset_password_with_invalid_token(self, client: TestClient, session: Session):
        """Test that invalid tokens don't work"""
        # Try with a completely invalid token
        response = client.get("/reset?token=invalid_token_12345")
        assert response.status_code == 400
        assert "Invalid or Expired Token" in response.text