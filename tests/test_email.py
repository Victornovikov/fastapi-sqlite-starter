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


@patch('app.email_client.resend.Emails.send')
def test_send_email_with_all_options(mock_send):
    """Test sending email with all optional parameters."""
    mock_send.return_value = {"id": "email_456", "status": "sent"}

    client = EmailClient(
        api_key="test_key",
        from_email="noreply@example.com",
        from_name="Test App"
    )

    result = client.send(
        to=["user@example.com"],
        subject="Test Subject",
        html="<p>HTML content</p>",
        text="Plain text content",
        reply_to="reply@example.com",
        tags=[{"name": "test", "value": "tag"}],
        idempotency_key="unique_key_123"
    )

    assert result["id"] == "email_456"
    mock_send.assert_called_once()

    # Verify all parameters were passed correctly
    call_args = mock_send.call_args[0][0]
    assert call_args["from"] == "Test App <noreply@example.com>"
    assert call_args["to"] == ["user@example.com"]
    assert call_args["subject"] == "Test Subject"
    assert call_args["html"] == "<p>HTML content</p>"
    assert call_args["text"] == "Plain text content"
    assert call_args["reply_to"] == "reply@example.com"
    assert call_args["tags"] == [{"name": "test", "value": "tag"}]

    # Verify idempotency key was passed
    options = mock_send.call_args[0][1]
    assert options == {"idempotency_key": "unique_key_123"}


def test_get_email_client_without_api_key():
    """Test get_email_client returns None when API key not configured."""
    with patch('app.email_client.get_settings') as mock_settings:
        mock_settings.return_value = MagicMock(
            resend_api_key=None
        )

        # Clear the cache first
        from app.email_client import get_email_client
        get_email_client.cache_clear()

        client = get_email_client()
        assert client is None