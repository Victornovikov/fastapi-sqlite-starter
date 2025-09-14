# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Logging
The application includes comprehensive centralized logging configured in `app/logging_config.py`:

```bash
# View real-time logs
tail -f logs/app.log

# Search for specific events
grep "WARNING\|ERROR" logs/app.log
grep "login" logs/app.log
grep "CSRF" logs/app.log

# Analyze authentication events
grep "app.routers.auth" logs/app.log

# Check rate limiting events
grep "Rate limit exceeded" logs/app.log
```

**Log Configuration** (via environment variables):
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `LOG_DIR`: Directory for log files (default: logs)
- `LOG_FILE`: Log filename (default: app.log)
- `LOG_MAX_BYTES`: Max size before rotation (default: 5MB)
- `LOG_BACKUP_COUNT`: Number of backup files to keep (default: 5)
- `LOG_TO_CONSOLE`: Enable console logging (default: True)

**Log Format**: `YYYY-MM-DD HH:MM:SS [LEVEL] module.name: message`

**What gets logged**:
- Authentication events (login, registration, failures)
- Rate limiting violations with IP addresses
- CSRF validation failures
- Password reset requests and completions
- Email sending and delivery status
- User profile access and updates
- Admin operations and unauthorized access attempts
- Database operations and errors
- Webhook events and processing

### Running the Application

#### Development Mode
```bash
# Development mode with auto-reload (run from project root)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode (direct uvicorn)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Production Deployment (SystemD Service)
```bash
# Deploy production setup (run from project root as root)
./deploy/deploy.sh --api-token YOUR_CLOUDFLARE_API_TOKEN [--domain your-domain.com]

# Service management (can run from any directory)
sudo systemctl start fastapi-app      # Start the service
sudo systemctl stop fastapi-app       # Stop the service
sudo systemctl restart fastapi-app    # Restart the service
sudo systemctl status fastapi-app     # Check service status
sudo systemctl enable fastapi-app     # Enable auto-start on boot

# View logs
sudo journalctl -u fastapi-app -f     # Follow logs in real-time
sudo journalctl -u fastapi-app --since "10 minutes ago"  # Recent logs
```

**Auto-restart behavior:**
- **Development**: `--reload` flag restarts on file changes
- **Production**: SystemD `Restart=always` automatically restarts on crashes
- Service is created at `/etc/systemd/system/fastapi-app.service` by deploy script
- Production uses Gunicorn with Uvicorn workers for better reliability

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_register_user -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto
```

#### ⚠️ Critical Testing Guidelines

**MUST READ before modifying tests or authentication code:**

**Remember: This is a WEB APP with cookies, not a REST API with headers!**

1. **Cookie Isolation for Multiple Users**
   - NEVER use the same TestClient for different users in tests
   - Each user MUST have their own TestClient instance to prevent cookie contamination
   ```python
   # ✅ CORRECT
   alice_client = TestClient(client.app)
   bob_client = TestClient(client.app)

   # ❌ WRONG - causes security test failures
   # Using same client for both users causes cookie overwrite
   ```

2. **Database Engine Override**
   - In `load_user()` or any function needing test database access:
   ```python
   # ✅ CORRECT - respects test database override
   import app.database
   db = Session(app.database.engine)

   # ❌ WRONG - bypasses test database
   from app.database import engine
   ```

3. **Rate Limits in Tests**
   - Registration: 5/minute limit
   - Login: 10/minute limit
   - Password reset: 3/minute limit
   - Tests MUST stay under these limits or explicitly reset the rate limiter

4. **Datetime Handling**
   - Always use `datetime.now(timezone.utc)` not `datetime.utcnow()`
   - SQLite stores naive datetimes - handle accordingly in tests

5. **CSRF Token Consistency**
   - Always use cookie name: `csrftoken` (not `csrf`)
   - Ensure consistency between app code and tests

See `tests.md` for comprehensive testing documentation and troubleshooting.

### Common Misconceptions to Avoid

1. **"It's a REST API"** - No, it's a web app with HTML/HTMX as the primary interface
2. **"Use Authorization headers"** - Web browsers use cookies; headers are for API clients
3. **"Return JSON errors"** - UI routes should return HTML fragments with error messages
4. **"Tokens in localStorage"** - This app uses secure HttpOnly cookies, not localStorage
5. **"Stateless authentication"** - This uses server-side sessions via JWT in cookies

### When Working on This App

- **For UI features**: Think HTML responses, CSRF tokens, cookie auth
- **For API features**: Think JSON responses, optional header auth
- **For testing**: Each user needs their own TestClient (cookies don't isolate)
- **For auth flow**: Check cookies first, then headers (fastapi-login's behavior)

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Architecture Overview

### ⚠️ CRITICAL: This is a Web App, NOT a REST API

**This is a cookie-based HTMX web application**, not a typical REST API. Understanding this is crucial:

1. **Primary Interface**: HTML pages with HTMX for dynamic updates
2. **Authentication**: Cookie-based sessions (not JWT in headers)
3. **API Endpoints**: Secondary - mainly for compatibility/mobile apps
4. **Form Submissions**: Use CSRF tokens and return HTML fragments
5. **User Experience**: Server-side rendered with progressive enhancement

### Why This Matters

- **Cookies are primary**: The app uses `access-token` cookies for auth, not Authorization headers
- **HTMX drives interactions**: Forms submit via HTMX, expecting HTML fragments or HX-Redirect headers
- **UI routes return HTML**: `/login`, `/dashboard`, `/profile` return HTML pages, not JSON
- **API routes are secondary**: `/auth/token` exists for API compatibility but the web UI uses `/auth/login`
- **fastapi-login behavior**: Cookies take precedence over headers when both are present

### Core Design Pattern
This is a FastAPI application using **fastapi-login** for authentication with cookie-based sessions. The architecture follows a layered approach:

1. **Routers Layer** (`app/routers/`) - HTTP endpoints that handle requests/responses
2. **Authentication Layer** (`app/login_manager.py`) - fastapi-login configuration and user management
3. **Security Layer** (`app/security.py`) - CSRF protection and password reset tokens
4. **Data Layer** (`app/models.py`, `app/database.py`) - SQLModel ORM with SQLite database
5. **Validation Layer** (`app/schemas.py`) - Pydantic models for request/response validation

### FastAPI-Login Authentication Implementation

#### Authentication Flow
1. **User Registration** (`POST /auth/register`)
   - Accepts: email, password, full_name
   - Validates uniqueness of email
   - Hashes password using bcrypt with salt rounds
   - Stores user in SQLite database
   - Returns: UserResponse (without password)

2. **User Login** (`POST /auth/token` for API, `POST /auth/login` for UI)
   - Accepts: OAuth2PasswordRequestForm (username field contains email, password)
   - Authenticates against hashed password in database
   - Creates JWT token using fastapi-login's LoginManager
   - Sets HttpOnly cookie with token
   - Supports "Remember Me" (30-day expiry vs standard session)
   - Returns: `{"access_token": token, "token_type": "bearer"}` for API

3. **Token Validation**
   - fastapi-login automatically extracts token from cookie or header
   - Token signature verified by LoginManager
   - User loaded via `@manager.user_loader()` decorator
   - Checks user.is_active flag automatically
   - Returns 401 (InvalidCredentialsException) if invalid

4. **Protected Endpoint Access**
   - Use `Depends(manager)` for authentication
   - Automatically validates token and loads user object
   - Support for optional authentication via `get_current_user_optional()`

### Key Dependencies and Their Roles
- **SQLModel**: Type-safe ORM that combines SQLAlchemy with Pydantic
- **fastapi-login**: Complete authentication solution with JWT, session management, and remember-me
- **passlib[bcrypt]**: Password hashing
- **slowapi**: Rate limiting for authentication endpoints

### Important Module Locations
Key functions and where to find them (for imports):
- `verify_password`, `get_password_hash`, `authenticate_user` → `app.login_manager`
- `generate_csrf_token`, `verify_csrf`, `sha256_hex` → `app.security`
- `User`, `PasswordResetToken` models → `app.models`
- `get_session`, `engine` → `app.database`
- Rate limiters → `app.rate_limit`

### Database Session Management
- Uses dependency injection via `get_session()` in `database.py`
- Sessions are yielded per request to ensure proper cleanup
- SQLite configured with `check_same_thread=False` for FastAPI compatibility

### Configuration Management
- Settings loaded from environment variables via `pydantic-settings`
- Config cached using `@lru_cache()` decorator
- Defaults provided in `app/config.py`, overridable via `.env` file
- Key settings:
  - `SECRET_KEY`: Used by fastapi-login for JWT signing
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: Default session duration (30 minutes)
  - `ENVIRONMENT`: Controls cookie security settings

### Testing Architecture
- Tests use in-memory SQLite database (via `StaticPool`)
- Database dependency injection overridden in tests
- Each test gets a fresh database instance
- Test fixtures defined in `tests/conftest.py`

### Security Considerations
- Passwords never stored in plain text
- JWT secret key must be changed in production (min 32 characters)
- Token expiration set to 30 minutes by default
- User isolation enforced - users can only access their own data
- Superuser flag for admin functionality
- **CSRF Protection**: Double-submit cookie pattern implemented for all forms
- **Environment-aware security**: Cookie secure flag automatically set based on environment

## API Endpoints Structure

### Authentication Endpoints (Public)

#### `POST /auth/register`
- **Purpose**: Register a new user account
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "user@example.com",
    "password": "string",
    "full_name": "string (optional)"
  }
  ```
- **Response**: UserResponse model (200 OK)
- **Errors**: 400 if username/email already exists

#### `POST /auth/token`
- **Purpose**: OAuth2 compatible login endpoint
- **Request**: `application/x-www-form-urlencoded`
  - `username`: User's username
  - `password`: User's password
  - `grant_type`: "password" (optional)
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
  ```
- **Errors**: 401 if credentials invalid

### Protected Endpoints (Require JWT)

#### `GET /users/me`
- **Purpose**: Get current authenticated user's profile
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Full user object (excluding password)

#### `PUT /users/me`
- **Purpose**: Update current user's profile
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: UserUpdate model
- **Response**: Updated user object

#### `GET /users/` (Admin Only)
- **Purpose**: List all users in the system
- **Requirements**: Valid JWT + user.is_superuser = true
- **Response**: List of all users

## FastAPI-Login Implementation Details

### Core Components

#### 1. Login Manager (`app/login_manager.py`)
- **`manager`**: LoginManager instance configured with:
  - Cookie name: "access-token"
  - Support for both cookie and header authentication
  - Configurable expiry (default 30 minutes, extendable to 30 days)
- **`@manager.user_loader()`**: Decorator for loading users from database
- **`authenticate_user(db, email, password)`**: User credential verification
- **`get_current_user_optional(request, db)`**: Optional authentication for mixed routes
- **`get_password_hash(password)`**: Bcrypt password hashing
- **`verify_password(plain, hashed)`**: Password verification

#### 2. Security Module (`app/security.py`)
- **`generate_csrf_token()`**: Creates secure CSRF tokens
- **`set_csrf_cookie(response, token)`**: Sets CSRF cookie
- **`verify_csrf(request, form_token)`**: Validates CSRF tokens
- **`sha256_hex(s)`**: Hashes password reset tokens

#### 3. Configuration (`app/config.py`)
Key environment variables:
- `SECRET_KEY`: fastapi-login JWT signing key (min 32 characters for production)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Default session duration (30 minutes)
- `DATABASE_URL`: SQLite connection string
- `ENVIRONMENT`: Set to "production" for secure cookies over HTTPS
- `RESEND_API_KEY`: Optional email service for password resets

#### 4. CSRF Protection (`app/security.py`)
- **`generate_csrf_token()`**: Creates secure random CSRF tokens
- **`set_csrf_cookie(response, token)`**: Sets CSRF cookie (non-HttpOnly for JS access)
- **`verify_csrf(request, form_token)`**: Validates CSRF token from form matches cookie
- All UI forms require CSRF token in hidden field matching cookie value

### Authentication Methods

#### 1. Required Authentication (API & UI)
```python
from app.login_manager import manager

@router.get("/api/protected")
async def api_endpoint(user: User = Depends(manager)):
    return {"message": f"Hello {user.email}"}
```

#### 2. Optional Authentication (Mixed Routes)
```python
from app.login_manager import get_current_user_optional

@router.get("/public")
async def mixed_endpoint(user: Optional[User] = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user.email}"}
    return {"message": "Hello anonymous"}
```

#### 3. Remember Me Feature
```python
# In login handler
if remember_me == "true":
    expires = timedelta(days=30)  # Long-lived session
else:
    expires = timedelta(minutes=30)  # Standard session

access_token = manager.create_access_token(
    data={"sub": user.email},
    expires=expires
)
```

### Testing OAuth2 Authentication

#### Using curl
```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Login and get token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"

# Use token for protected endpoint
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer <your_token_here>"
```

#### Using Python requests
```python
import requests

# Login
response = requests.post("http://localhost:8000/auth/token",
    data={"username": "testuser", "password": "testpass123"})
token = response.json()["access_token"]

# Access protected endpoint
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/users/me", headers=headers)
print(response.json())
```

## Common Development Tasks

### Adding New Protected Endpoints
```python
from app.login_manager import manager
from app.models import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(manager)):
    return {"user": current_user}
```

### Adding Admin-Only Endpoints
```python
from app.login_manager import manager
from fastapi import HTTPException, status

async def get_admin_user(current_user: User = Depends(manager)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@router.delete("/admin/user/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(get_admin_user)):
    # Admin-only operation
    pass
```

### Modifying User Model
1. Update `app/models.py` with new fields
2. Update `app/schemas.py` with corresponding Pydantic schemas
3. Consider database migration strategy (currently recreates tables on startup)

### Key Features Provided by FastAPI-Login

1. **Automatic Token Management**
   - Token creation, validation, and decoding handled internally
   - Support for both cookies and Authorization headers
   - Configurable expiration times

2. **Remember Me Functionality**
   - Extended session duration (30 days) when checkbox selected
   - Secure cookie settings based on environment

3. **User Loading**
   - Decorator-based user loader (`@manager.user_loader()`)
   - Automatic user fetching from database
   - Active user validation

4. **Security Features**
   - HttpOnly cookies prevent XSS attacks
   - Secure flag for HTTPS environments
   - SameSite protection against CSRF
   - Built-in exception handling

5. **Rate Limiting** (via slowapi)
   - Login: 10/minute (UI), 5/minute (API)
   - Registration: 5/minute
   - Password reset: 3/minute