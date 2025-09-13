# FastAPI Centralized Logging Implementation

## Overview
This document outlines the COMPLETED implementation of production-ready centralized file logging for the FastAPI authentication application. The solution uses Python's standard logging library with rotating file handlers to capture all application events, HTTP requests, errors, and background tasks in a single, manageable log file.

## Implementation Status: ✅ COMPLETED (2025-09-13)

## Architecture Design

### Core Components
1. **Centralized Configuration** (`app/logging_config.py`)
   - Single source of truth for all logging configuration
   - RotatingFileHandler with 5MB max size and 5 backup files
   - Consistent formatting across all loggers
   - Integration with Uvicorn's built-in loggers

2. **Log File Structure**
   - Location: `logs/app.log`
   - Rotation: Automatic at 5MB threshold
   - Backups: `app.log.1` through `app.log.5`
   - Format: Plain text with structured fields

3. **Log Format**
   ```
   %(asctime)s [%(levelname)s] %(name)s: %(message)s
   ```
   Example:
   ```
   2025-09-13 10:30:45,123 [INFO] app.routers.auth: User registered: email=user@example.com
   ```

## Implementation Details

### Phase 1: Core Infrastructure

#### 1.1 Create Logging Configuration Module (`app/logging_config.py`)
```python
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Configure centralized logging for the entire application."""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Configure Uvicorn loggers
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
        logger.setLevel(getattr(logging, log_level))

    return file_handler
```

#### 1.2 Update Main Application (`app/main.py`)
- Import logging configuration at startup
- Add application lifecycle logging
- Ensure exception handlers log errors

### Phase 2: Authentication & Security Logging

#### 2.1 Authentication Routes (`app/routers/auth.py`)
Log Points:
- `POST /auth/register` - User registration attempts
  - SUCCESS: `User registered: email={email}, username={username}`
  - FAILURE: `Registration failed: email={email}, reason={reason}`
- `POST /auth/token` - API login attempts
  - SUCCESS: `API login successful: username={username}`
  - FAILURE: `API login failed: username={username}, reason={reason}`

#### 2.2 UI Authentication (`app/routers/ui.py`)
Log Points:
- `POST /auth/login` - Web login attempts
  - SUCCESS: `Web login successful: email={email}, remember_me={remember_me}, ip={ip}`
  - FAILURE: `Web login failed: email={email}, ip={ip}`
- `POST /auth/signup` - Web registration
  - SUCCESS: `Web signup: email={email}, full_name={full_name}`
  - FAILURE: `Web signup failed: email={email}, reason={reason}`
- `POST /auth/forgot` - Password reset requests
  - INFO: `Password reset requested: email={email}`
- `POST /auth/reset` - Password reset completion
  - SUCCESS: `Password reset completed: email={email}`
  - FAILURE: `Password reset failed: invalid_token`
- `POST /logout` - User logout
  - INFO: `User logged out: email={email}`

#### 2.3 Login Manager (`app/login_manager.py`)
Log Points:
- Token validation failures
  - WARNING: `Invalid token attempted: reason={reason}`
- User retrieval failures
  - WARNING: `User not found for token: email={email}`

#### 2.4 Security Module (`app/security.py`)
Log Points:
- CSRF validation failures
  - ERROR: `CSRF validation failed: expected={expected}, received={received}, ip={ip}`
- Token decode failures
  - WARNING: `Token decode failed: reason={reason}`

### Phase 3: User Operations Logging

#### 3.1 User Routes (`app/routers/users.py`)
Log Points:
- `GET /users/me` - Profile access
  - INFO: `Profile accessed: user={username}`
- `PUT /users/me` - Profile updates
  - INFO: `Profile updated: user={username}, fields={updated_fields}`
- `GET /users/` - Admin operations
  - INFO: `Admin user list accessed: admin={username}`
  - WARNING: `Unauthorized admin access attempt: user={username}`

### Phase 4: Email System Logging

#### 4.1 Email Client (`app/email_client.py`)
Enhance existing logging:
- Email send attempts
  - INFO: `Email queued: to={recipient}, subject={subject}, template={template}`
  - ERROR: `Email send failed: to={recipient}, error={error}`
- Delivery confirmations
  - INFO: `Email delivered: to={recipient}, message_id={id}`

### Phase 5: Webhook Processing Logging

#### 5.1 Webhook Handlers (`app/webhooks.py`)
Enhance existing logging:
- Webhook receipt
  - INFO: `Resend webhook received: event={event_type}, email={email}`
- Processing results
  - WARNING: `Email bounce: email={email}, type={bounce_type}`
  - WARNING: `Spam complaint: email={email}`
  - INFO: `Email delivered via webhook: email={email}`
- Validation failures
  - ERROR: `Webhook signature validation failed: ip={ip}`

### Phase 6: Infrastructure Logging

#### 6.1 Database Operations (`app/database.py`)
Log Points:
- Database initialization
  - INFO: `Database initialized: url={masked_url}`
- Table creation
  - INFO: `Database tables created`
- Session lifecycle
  - DEBUG: `Database session created: id={session_id}`
  - DEBUG: `Database session closed: id={session_id}`

#### 6.2 Rate Limiting (`app/rate_limit.py`)
Log Points:
- Rate limit exceeded
  - WARNING: `Rate limit exceeded: endpoint={endpoint}, ip={ip}, limit={limit}`
- IP extraction
  - DEBUG: `Client IP extracted: ip={ip}, source={header_or_direct}`

### Phase 7: Directory Structure & Configuration

#### 7.1 Create Log Directory
```bash
mkdir -p logs
touch logs/.gitkeep
```

#### 7.2 Update .gitignore
Add:
```
# Logs
logs/*.log
logs/*.log.*
!logs/.gitkeep
```

#### 7.3 Set File Permissions
```bash
chmod 750 logs
chmod 640 logs/*.log
```

## Log Level Guidelines

### Production Configuration
| Level | Usage | Examples |
|-------|-------|----------|
| **INFO** | Normal operations | User login, email sent, profile updated |
| **WARNING** | Notable events | Failed login, rate limit hit, email bounce |
| **ERROR** | Errors requiring attention | Database connection lost, service unavailable |
| **CRITICAL** | System failures | Configuration missing, database corruption |

### Development Configuration
- Set to **DEBUG** for detailed traces
- Include SQL queries, request bodies, token contents (masked)
- Disable in production for performance

## Security Considerations

### Sensitive Data Handling
1. **Never log**:
   - Plain text passwords
   - Full authentication tokens
   - Complete credit card numbers
   - Full API keys

2. **Always mask**:
   - Token: Show first/last 4 characters only
   - Email: Can log in full for audit purposes
   - IP addresses: Log in full for security tracking

3. **Truncate**:
   - Long request bodies (max 500 chars)
   - Stack traces in production (show only relevant frames)

### Log Message Examples
```python
# Good - masked sensitive data
logger.info(f"Password reset token generated: email={email}, token_hash={token_hash[:8]}...")

# Bad - exposes sensitive data
logger.info(f"Password reset token: {full_token}")

# Good - structured for parsing
logger.warning(f"Login failed: email={email}, reason=invalid_password, ip={ip}, attempts={attempts}")

# Bad - unstructured
logger.warning(f"Bad login from {ip} for {email}")
```

## Implementation Checklist

### Phase 1: Core Setup
- [x] Create `app/logging_config.py`
- [x] Update `app/main.py` with logging initialization
- [x] Create `logs/` directory with proper permissions
- [x] Update `.gitignore`

### Phase 2: Authentication
- [x] Add logging to `app/routers/auth.py`
- [x] Add logging to `app/routers/ui.py`
- [x] Add logging to `app/login_manager.py`
- [x] Add logging to `app/security.py`

### Phase 3: User Operations
- [x] Add logging to `app/routers/users.py`

### Phase 4: Email System
- [x] Enhance logging in `app/email_client.py`

### Phase 5: Webhooks
- [x] Enhance logging in `app/webhooks.py`

### Phase 6: Infrastructure
- [x] Add logging to `app/database.py`
- [x] Add logging to `app/rate_limit.py` (via main.py)

### Phase 7: Testing
- [x] Test successful user registration
- [x] Test failed login attempts
- [x] Test rate limiting
- [x] Test email sending
- [x] Test log rotation capability
- [x] Verify no sensitive data in logs

## Testing Strategy

### Functional Tests
1. **Authentication Flow**
   - Register new user → Check INFO log
   - Login with wrong password → Check WARNING log
   - Successful login → Check INFO log
   - Logout → Check INFO log

2. **Rate Limiting**
   - Exceed rate limit → Check WARNING log with IP

3. **Email Operations**
   - Send password reset → Check INFO log
   - Email delivery webhook → Check INFO log
   - Email bounce webhook → Check WARNING log

### Log Rotation Test
1. Generate logs exceeding 5MB
2. Verify creation of `app.log.1`
3. Confirm continued logging to new `app.log`
4. Check that old backups are removed after 5 rotations

### Performance Validation
1. Measure response time with/without logging
2. Ensure async operations aren't blocked
3. Verify log write doesn't impact request handling

## Monitoring & Maintenance

### Log Analysis Tools
Consider integrating:
- `tail -f logs/app.log` for real-time monitoring
- `grep` patterns for specific event types
- Log aggregation tools (ELK, Splunk) for production

### Regular Maintenance
- Weekly: Review log sizes and rotation
- Monthly: Analyze error patterns
- Quarterly: Adjust log levels based on needs

### Alert Patterns
Set up monitoring for:
- Multiple failed login attempts from same IP
- Unusual number of 500 errors
- Database connection failures
- Email service failures

## Example Log Output (From Actual Tests)

```
2025-09-13 14:34:48 [INFO] app.routers.auth: Registration attempt: email=admin@example.com, ip=unknown
2025-09-13 14:34:48 [INFO] app.routers.auth: User registered successfully: email=admin@example.com, full_name=Admin User, ip=unknown
2025-09-13 14:34:48 [INFO] app.routers.auth: API login attempt: username=admin@example.com, ip=unknown
2025-09-13 14:34:48 [INFO] app.routers.auth: API login successful: email=admin@example.com, ip=unknown, token_expires_minutes=30
2025-09-13 14:34:55 [WARNING] app.routers.auth: Registration failed - email exists: email=duplicate@example.com, ip=unknown
2025-09-13 14:34:55 [WARNING] app.main: Client error: status=400, path=/auth/register, ip=unknown, detail=Email already registered
2025-09-13 14:34:54 [WARNING] slowapi: ratelimit 5 per 1 minute (unknown) exceeded at endpoint: /auth/register
2025-09-13 14:34:54 [WARNING] app.main: Rate limit exceeded: path=/auth/register, ip=unknown, limit=5 per 1 minute
2025-09-13 14:34:57 [ERROR] app.security: CSRF validation failed: expected=vali...oken, received=inva...oken, ip=unknown, path=/auth/login
2025-09-13 14:34:57 [ERROR] app.routers.ui: CSRF validation failed on login: email=test@example.com, ip=unknown, error=403: CSRF verification failed
2025-09-13 14:34:58 [INFO] app.routers.ui: Web signup successful: email=new@example.com, full_name=New User, ip=unknown
2025-09-13 14:34:58 [INFO] app.email_client: Sending password reset email: to=user@example.com, user_name=John Doe, template=password_reset
2025-09-13 14:34:58 [INFO] app.email_client: Email queued: to=user@example.com, subject=Reset Your Password, message_id=email_123, template=custom
2025-09-13 14:35:03 [WARNING] app.login_manager: Authentication failed - inactive user: email=inactive@example.com
2025-09-13 14:35:04 [INFO] app.routers.ui: Password reset requested: email=test@example.com, ip=unknown
2025-09-13 14:35:04 [INFO] app.routers.ui: Password reset attempt: token=dgZo...yroc, ip=unknown
2025-09-13 14:35:05 [INFO] app.routers.ui: Password reset completed: email=test@example.com, ip=unknown
```

## Conclusion

This comprehensive logging implementation provides:
- Complete visibility into application behavior
- Security audit trail for compliance
- Performance monitoring capabilities
- Debugging information for troubleshooting
- Scalable architecture for growth

The phased approach ensures systematic implementation while maintaining application stability throughout the process.