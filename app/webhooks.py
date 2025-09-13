"""
Webhook handlers for external services.
"""
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from svix.webhooks import Webhook, WebhookVerificationError
from sqlmodel import Session, select
from typing import Dict, Any
import logging

from app.database import get_session
from app.models import User
from app.config import get_settings
from app.logging_config import get_client_ip

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

    client_ip = get_client_ip(request)

    # Check if webhook secret is configured
    if not settings.resend_webhook_secret:
        logger.warning(
            f"Resend webhook called but RESEND_WEBHOOK_SECRET not configured, ip={client_ip}"
        )
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
        logger.error(
            f"Webhook signature validation failed: ip={client_ip}, error={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    # Process the webhook event
    event_type = verified_payload.get("type")
    data = verified_payload.get("data", {})

    message_id = data.get("email_id", "unknown")
    logger.info(
        f"Resend webhook received: event={event_type}, message_id={message_id}, ip={client_ip}"
    )

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
                logger.warning(
                    f"Email bounce: email={email}, type=hard_bounce, "
                    f"user_exists={user is not None}, message_id={message_id}"
                )
                # TODO: Implement email validation flag
                # user.email_valid = False
                # session.commit()

    elif event_type == "email.complained":
        # Handle spam complaint
        email = data.get("to", [None])[0]
        if email:
            logger.warning(
                f"Spam complaint: email={email}, message_id={message_id}"
            )
            # TODO: Add user to suppression list
            # Could set a flag in User model or maintain separate suppression table

    elif event_type == "email.delivered":
        # Log successful delivery
        email = data.get("to", [None])[0]
        logger.info(
            f"Email delivered via webhook: email={email}, message_id={message_id}"
        )

    elif event_type == "email.sent":
        # Email was sent (but not necessarily delivered)
        email = data.get("to", [None])[0]
        logger.info(
            f"Email sent notification: email={email}, message_id={message_id}"
        )

    # Return 204 No Content for successful processing
    return