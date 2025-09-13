# Resend Email Integration Implementation Plan

## Overview
This plan details the integration of Resend email service into the existing FastAPI authentication system to enable actual email sending for password reset functionality. The application already has a complete password reset flow but currently only logs reset links to the console.

## Current State
- Password reset flow exists in `/app/routers/ui.py` (lines 266-408)
- Token generation uses `secrets.token_urlsafe(32)` with SHA256 hashing
- Tokens stored in `PasswordResetToken` table with 1-hour expiration
- TODO comment at lines 298-299 where email sending should be implemented
- CSRF protection already implemented on all forms

## Implementation Steps

### Part 1: Domain Verification (Manual Setup)

#### Prerequisites
- [ ] Create a Resend account at https://resend.com
- [ ] Access to your domain's DNS settings

#### DNS Configuration
- [ ] Add SPF record to your domain:
  ```
  Type: TXT
  Name: @ (or your subdomain)
  Value: v=spf1 include:amazonses.com ~all
  ```
- [ ] Add DKIM records provided by Resend (will be 3 CNAME records)
- [ ] Verify domain in Resend dashboard
- [ ] (Optional) Configure DMARC record for enhanced deliverability:
  ```
  Type: TXT
  Name: _dmarc
  Value: v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
  ```

### Part 2: Key Management

#### Install Dependencies
- [x] Update `requirements.txt` with new dependencies:
  ```txt
  resend==0.7.2
  svix==1.21.0
  ```
- [x] Run `pip install -r requirements.txt`

#### Create Key Provisioning Script
- [x] Create directory `scripts/` if it doesn't exist
- [x] Create `scripts/create_resend_key.py`:
  ```python
  #!/usr/bin/env python3
  """
  One-time script to create a sending_access scoped API key.
  This uses an admin key that should NEVER be stored in the application.

  Usage:
    RESEND_ADMIN_API_KEY=re_full_access_xxx python scripts/create_resend_key.py
  """
  import os
  import sys
  import resend

  def main():
      admin_key = os.environ.get("RESEND_ADMIN_API_KEY")
      if not admin_key:
          print("Error: RESEND_ADMIN_API_KEY environment variable not set")
          print("Get your admin key from: https://resend.com/api-keys")
          sys.exit(1)

      resend.api_key = admin_key

      try:
          # Create a sending-only key for the application
          create_params = {
              "name": "fastapi-app-sender",
              "permission": "sending_access"
          }

          created = resend.ApiKeys.create(params=create_params)

          print("✅ API Key created successfully!")
          print("\nAdd this to your .env file:")
          print(f"RESEND_API_KEY={created['token']}")
          print("\n⚠️  This token is shown only once. Store it securely!")

      except Exception as e:
          print(f"Error creating API key: {e}")
          sys.exit(1)

  if __name__ == "__main__":
      main()
  ```

#### Generate Production Key
- [ ] Get admin API key from Resend dashboard
- [ ] Run the provisioning script:
  ```bash
  RESEND_ADMIN_API_KEY=re_xxx python scripts/create_resend_key.py
  ```
- [ ] Save the generated `sending_access` key securely
- [ ] Never commit the admin key to version control

### Part 3: Storage Configuration

#### Update Environment Variables
- [x] Update `.env.example`:
  ```env
  # Existing variables...

  # Email Configuration
  RESEND_API_KEY=re_xxx_change_this
  EMAIL_FROM=Your App <noreply@yourdomain.com>
  EMAIL_FROM_NAME=Your App Name
  RESET_URL_BASE=https://yourdomain.com/reset

  # Optional: Webhook verification
  RESEND_WEBHOOK_SECRET=whsec_xxx_change_this
  ```

- [ ] Update your actual `.env` file with real values:
  - `RESEND_API_KEY`: The sending_access key from Part 2
  - `EMAIL_FROM`: Must use your verified domain
  - `RESET_URL_BASE`: Your production URL

#### Update Configuration Schema
- [x] Update `app/config.py`:
  ```python
  from pydantic_settings import BaseSettings
  from pydantic import EmailStr, AnyUrl, SecretStr
  from typing import Optional
  from functools import lru_cache


  class Settings(BaseSettings):
      # Existing settings...
      database_url: str = "sqlite:///./app.db"
      secret_key: str = "your-secret-key-change-this-in-production"
      algorithm: str = "HS256"
      access_token_expire_minutes: int = 30
      refresh_token_expire_days: int = 7
      environment: str = "development"

      # Email settings
      resend_api_key: SecretStr
      email_from: EmailStr = "noreply@example.com"
      email_from_name: str = "FastAPI App"
      reset_url_base: AnyUrl = "http://localhost:8000/reset"

      # Optional webhook secret
      resend_webhook_secret: Optional[SecretStr] = None

      @property
      def cookie_secure(self) -> bool:
          """Return True if cookies should use secure flag (HTTPS only)"""
          return self.environment == "production"

      class Config:
          env_file = ".env"
          extra = "ignore"


  @lru_cache()
  def get_settings():
      return Settings()
  ```

### Part 4: App Wiring

#### Create Email Client
- [x] Create `app/email_client.py`:
  ```python
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
              logger.info(f"Email sent successfully to {to[0]}")
              return response
          except Exception as e:
              logger.error(f"Failed to send email to {to[0]}: {str(e)}")
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
      return EmailClient(
          api_key=settings.resend_api_key.get_secret_value(),
          from_email=str(settings.email_from),
          from_name=settings.email_from_name
      )
  ```

#### Update Password Reset Handler
- [x] Update `app/routers/ui.py` (replace lines 298-299):
  ```python
  # Add these imports at the top of the file
  from fastapi import BackgroundTasks
  from app.email_client import get_email_client

  # Update the handle_forgot_password function signature to include BackgroundTasks
  @router.post("/auth/forgot", response_class=HTMLResponse)
  async def handle_forgot_password(
      request: Request,
      email: str = Form(...),
      csrf: str = Form(...),
      session: Session = Depends(get_session),
      background_tasks: BackgroundTasks = BackgroundTasks()
  ):
      """Handle forgot password form submission"""
      # Verify CSRF token
      verify_csrf(request, csrf)

      # Always return success to prevent email enumeration
      user = session.exec(select(User).where(User.email == email)).first()

      if user:
          # Generate reset token
          raw_token = secrets.token_urlsafe(32)

          # Create token record
          reset_token = PasswordResetToken(
              user_id=user.id,
              token_hash=sha256_hex(raw_token),
              expires_at=datetime.utcnow() + timedelta(hours=1)
          )
          session.add(reset_token)
          session.commit()

          # Send email in background (non-blocking)
          try:
              email_client = get_email_client()
              background_tasks.add_task(
                  email_client.send_password_reset,
                  email=email,
                  token=raw_token,
                  user_name=user.full_name or user.username
              )
          except Exception as e:
              # Log error but don't expose it to user
              logger.error(f"Failed to queue password reset email: {e}")
              # Continue anyway to prevent enumeration

      # Always return success message
      return templates.TemplateResponse(
          "fragments/forgot_success.html",
          {
              "request": request,
              "message": "If an account exists with that email, you will receive a password reset link."
          }
      )
  ```

#### Add Logging Configuration
- [x] Add logging setup in `app/routers/ui.py`:
  ```python
  import logging

  logger = logging.getLogger(__name__)
  ```

### Part 5: Webhooks (Optional but Recommended)

#### Create Webhook Handler
- [x] Create `app/webhooks.py`:
  ```python
  """
  Webhook handlers for external services.
  """
  from fastapi import APIRouter, Request, Response, HTTPException, status
  from svix.webhooks import Webhook, WebhookVerificationError
  from sqlmodel import Session, select
  from typing import Dict, Any
  import logging

  from app.database import get_session
  from app.models import User
  from app.config import get_settings

  logger = logging.getLogger(__name__)
  router = APIRouter(prefix="/webhooks", tags=["webhooks"], include_in_schema=False)


  @router.post("/resend", status_code=status.HTTP_204_NO_CONTENT)
  async def resend_webhook(
      request: Request,
      response: Response,
      session: Session = Depends(get_session)
  ):
      """
      Handle Resend webhook events.

      Events handled:
      - email.sent: Email was successfully sent
      - email.delivered: Email was delivered to recipient
      - email.bounced: Email bounced (permanent failure)
      - email.complained: Recipient marked as spam
      - email.opened: Email was opened (if tracking enabled)
      - email.clicked: Link was clicked (if tracking enabled)
      """
      settings = get_settings()

      # Check if webhook secret is configured
      if not settings.resend_webhook_secret:
          logger.warning("Resend webhook called but RESEND_WEBHOOK_SECRET not configured")
          response.status_code = status.HTTP_501_NOT_IMPLEMENTED
          return {"error": "Webhook not configured"}

      # Get raw body and headers for signature verification
      payload = await request.body()
      headers = request.headers

      # Verify webhook signature
      try:
          webhook = Webhook(settings.resend_webhook_secret.get_secret_value())
          verified_payload = webhook.verify(payload, headers)
      except WebhookVerificationError as e:
          logger.error(f"Webhook verification failed: {e}")
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="Invalid webhook signature"
          )

      # Process the webhook event
      event_type = verified_payload.get("type")
      data = verified_payload.get("data", {})

      logger.info(f"Received Resend webhook: {event_type}")

      # Handle different event types
      if event_type == "email.bounced":
          # Handle bounced email
          email = data.get("to", [None])[0]
          bounce_type = data.get("bounce", {}).get("type")

          if email and bounce_type == "hard_bounce":
              # Mark user's email as invalid to prevent future sends
              user = session.exec(select(User).where(User.email == email)).first()
              if user:
                  # You might want to add an 'email_valid' field to User model
                  logger.warning(f"Hard bounce for user {user.username}: {email}")
                  # TODO: Implement email validation flag

      elif event_type == "email.complained":
          # Handle spam complaint
          email = data.get("to", [None])[0]
          if email:
              logger.warning(f"Spam complaint received for: {email}")
              # TODO: Add user to suppression list

      elif event_type == "email.delivered":
          # Log successful delivery
          email = data.get("to", [None])[0]
          logger.info(f"Email delivered successfully to: {email}")

      elif event_type == "email.sent":
          # Email was sent (but not necessarily delivered)
          email = data.get("to", [None])[0]
          logger.info(f"Email sent to: {email}")

      # Return 204 No Content for successful processing
      return
  ```

#### Register Webhook Router
- [x] Update `app/main.py`:
  ```python
  from app.routers import auth, users, ui
  from app import webhooks  # Add this import

  # ... existing code ...

  app.include_router(auth.router)
  app.include_router(users.router)
  app.include_router(ui.router)
  app.include_router(webhooks.router)  # Add this line
  ```

#### Configure Webhook in Resend Dashboard
- [ ] Go to Resend Dashboard > Webhooks
- [ ] Add endpoint URL: `https://yourdomain.com/webhooks/resend`
- [ ] Select events to track:
  - [ ] email.sent
  - [ ] email.delivered
  - [ ] email.bounced
  - [ ] email.complained
- [ ] Copy the webhook signing secret
- [ ] Add to `.env`: `RESEND_WEBHOOK_SECRET=whsec_xxx`

### Part 6: Testing

#### Unit Tests
- [x] Create `tests/test_email.py`:
  ```python
  """
  Tests for email functionality.
  """
  import pytest
  from unittest.mock import Mock, patch, MagicMock
  from app.email_client import EmailClient


  def test_email_client_initialization():
      """Test EmailClient initialization."""
      client = EmailClient(
          api_key="test_key",
          from_email="test@example.com",
          from_name="Test App"
      )
      assert client.from_email == "test@example.com"
      assert client.from_name == "Test App"
      assert client.sender == "Test App <test@example.com>"


  @patch('app.email_client.resend.Emails.send')
  def test_send_password_reset(mock_send):
      """Test sending password reset email."""
      mock_send.return_value = {"id": "email_123", "status": "sent"}

      client = EmailClient(
          api_key="test_key",
          from_email="noreply@example.com",
          from_name="Test App"
      )

      with patch('app.email_client.get_settings') as mock_settings:
          mock_settings.return_value = MagicMock(
              reset_url_base="https://example.com/reset"
          )

          result = client.send_password_reset(
              email="user@example.com",
              token="test_token_123",
              user_name="John Doe"
          )

      assert result["id"] == "email_123"
      mock_send.assert_called_once()

      # Verify idempotency key is set to token
      call_args = mock_send.call_args
      assert call_args[0][1] == {"idempotency_key": "test_token_123"}


  @patch('app.email_client.resend.Emails.send')
  def test_send_email_with_error(mock_send):
      """Test email sending error handling."""
      mock_send.side_effect = Exception("API Error")

      client = EmailClient(
          api_key="test_key",
          from_email="noreply@example.com",
          from_name="Test App"
      )

      with pytest.raises(Exception) as exc_info:
          client.send(
              to=["user@example.com"],
              subject="Test",
              html="<p>Test</p>"
          )

      assert "API Error" in str(exc_info.value)
  ```

#### Integration Tests
- [x] Create `tests/test_password_reset_integration.py`:
  ```python
  """
  Integration tests for password reset flow with email.
  """
  import pytest
  from unittest.mock import patch, MagicMock
  from fastapi.testclient import TestClient


  def test_forgot_password_sends_email(client: TestClient, test_user):
      """Test that forgot password triggers email send."""
      with patch('app.routers.ui.get_email_client') as mock_client:
          mock_email_client = MagicMock()
          mock_client.return_value = mock_email_client

          # Get CSRF token
          response = client.get("/forgot")
          csrf_token = response.cookies.get("csrf_token")

          # Submit forgot password form
          response = client.post(
              "/auth/forgot",
              data={
                  "email": test_user.email,
                  "csrf": csrf_token
              },
              headers={"Cookie": f"csrf_token={csrf_token}"}
          )

          assert response.status_code == 200
          assert "If an account exists" in response.text

          # Verify email client was called
          # Note: Called via background task, so may need to wait
          mock_email_client.send_password_reset.assert_called()


  def test_forgot_password_no_user_no_email(client: TestClient):
      """Test that non-existent email doesn't send but returns success."""
      with patch('app.routers.ui.get_email_client') as mock_client:
          mock_email_client = MagicMock()
          mock_client.return_value = mock_email_client

          # Get CSRF token
          response = client.get("/forgot")
          csrf_token = response.cookies.get("csrf_token")

          # Submit with non-existent email
          response = client.post(
              "/auth/forgot",
              data={
                  "email": "nonexistent@example.com",
                  "csrf": csrf_token
              },
              headers={"Cookie": f"csrf_token={csrf_token}"}
          )

          assert response.status_code == 200
          assert "If an account exists" in response.text

          # Verify email was NOT sent
          mock_email_client.send_password_reset.assert_not_called()
  ```

#### Manual Testing Checklist
- [ ] Test password reset flow end-to-end:
  1. [ ] Request password reset
  2. [ ] Check email received
  3. [ ] Click reset link
  4. [ ] Set new password
  5. [ ] Login with new password
- [ ] Test email error handling (invalid API key)
- [ ] Test webhook signature verification
- [ ] Test idempotency (multiple clicks don't send multiple emails)

### Part 7: Deployment Checklist

#### Environment Variables
- [ ] Set `ENVIRONMENT=production` in production
- [ ] Ensure `RESEND_API_KEY` is set with sending_access key
- [ ] Verify `EMAIL_FROM` uses verified domain
- [ ] Set `RESET_URL_BASE` to production URL
- [ ] Configure `RESEND_WEBHOOK_SECRET` if using webhooks

#### Security Checklist
- [ ] Never log API keys or tokens
- [ ] Ensure cookies use secure flag in production
- [ ] Verify webhook signatures are validated
- [ ] Test rate limiting on password reset endpoint
- [ ] Confirm email enumeration protection works

#### Monitoring
- [ ] Set up logging for email send failures
- [ ] Monitor Resend dashboard for bounce rates
- [ ] Set up alerts for high bounce/complaint rates
- [ ] Track webhook processing errors

## Rollback Plan

If issues arise with email sending:

1. **Quick Disable**: Comment out email sending code, keeping logging
2. **Revert Dependencies**: Remove `resend` and `svix` from requirements
3. **Environment**: Remove Resend-related environment variables
4. **Clean Code**: Remove email_client.py and webhooks.py if needed

## Success Criteria

- [ ] Password reset emails are sent successfully
- [ ] Emails arrive within 1-2 minutes
- [ ] Reset links work correctly
- [ ] No duplicate emails sent (idempotency works)
- [ ] Webhook events are processed
- [ ] Error handling doesn't expose user enumeration
- [ ] Production deployment successful

## Notes

- Resend free tier includes 3,000 emails/month and 100 emails/day
- Consider implementing rate limiting per user (e.g., max 3 reset requests per hour)
- For production, consider adding email templates for better maintainability
- Monitor delivery rates and adjust SPF/DKIM/DMARC as needed