"""
Email client for sending transactional emails via Resend.
"""
import resend
from typing import Dict, List, Optional, Any
from functools import lru_cache
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailClient:
    """Wrapper for Resend email service."""

    def __init__(self, api_key: str, from_email: str, from_name: str):
        """Initialize the email client with Resend API."""
        resend.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name
        self.sender = f"{from_name} <{from_email}>"

    def send(
        self,
        to: List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email using Resend API.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            html: HTML content of the email
            text: Plain text content (optional)
            reply_to: Reply-to email address (optional)
            tags: Metadata tags for tracking (optional)
            idempotency_key: Key to prevent duplicate sends (optional)

        Returns:
            Response from Resend API
        """
        params = {
            "from": self.sender,
            "to": to,
            "subject": subject,
            "html": html,
        }

        if text:
            params["text"] = text
        if reply_to:
            params["reply_to"] = reply_to
        if tags:
            params["tags"] = tags

        # Use idempotency key to prevent duplicate sends
        options = {"idempotency_key": idempotency_key} if idempotency_key else None

        try:
            response = resend.Emails.send(params, options)
            message_id = response.get('id', 'unknown')
            logger.info(
                f"Email queued: to={to[0]}, subject={subject}, "
                f"message_id={message_id}, template=custom"
            )
            return response
        except Exception as e:
            logger.error(
                f"Email send failed: to={to[0]}, subject={subject}, "
                f"error={str(e)}"
            )
            raise

    def send_password_reset(
        self,
        email: str,
        token: str,
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a password reset email.

        Args:
            email: Recipient email
            token: Reset token (raw, not hashed)
            user_name: User's display name (optional)

        Returns:
            Response from Resend API
        """
        settings = get_settings()
        reset_link = f"{settings.reset_url_base}?token={token}"

        # Personalize the greeting
        greeting = f"Hi {user_name}" if user_name else "Hi"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb; margin-bottom: 24px;">Reset Your Password</h2>

            <p>{greeting},</p>

            <p>We received a request to reset your password. Click the button below to create a new password:</p>

            <div style="text-align: center; margin: 32px 0;">
                <a href="{reset_link}"
                   style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: 500;">
                    Reset Password
                </a>
            </div>

            <p style="color: #666; font-size: 14px;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_link}" style="color: #2563eb; word-break: break-all;">{reset_link}</a>
            </p>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 32px 0;">

            <p style="color: #666; font-size: 14px;">
                This link will expire in 1 hour. If you didn't request a password reset,
                you can safely ignore this email.
            </p>

            <p style="color: #666; font-size: 14px; margin-top: 24px;">
                Best regards,<br>
                {self.from_name} Team
            </p>
        </body>
        </html>
        """

        text = f"""
        {greeting},

        We received a request to reset your password. Visit the link below to create a new password:

        {reset_link}

        This link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.

        Best regards,
        {self.from_name} Team
        """

        logger.info(
            f"Sending password reset email: to={email}, "
            f"user_name={user_name}, template=password_reset"
        )

        return self.send(
            to=[email],
            subject="Reset Your Password",
            html=html,
            text=text,
            tags=[
                {"name": "type", "value": "password_reset"},
                {"name": "app", "value": "fastapi-auth"}
            ],
            idempotency_key=token  # Use token as idempotency key
        )


@lru_cache()
def get_email_client() -> EmailClient:
    """Get a cached instance of the email client."""
    settings = get_settings()

    # Check if email is configured
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured. Email sending will be disabled.")
        return None

    logger.info(
        f"Email client initialized: from={settings.email_from}, "
        f"from_name={settings.email_from_name}"
    )

    return EmailClient(
        api_key=settings.resend_api_key.get_secret_value(),
        from_email=str(settings.email_from),
        from_name=settings.email_from_name
    )