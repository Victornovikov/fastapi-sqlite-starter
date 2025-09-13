# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

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

### Core Design Pattern
This is a FastAPI application using OAuth2 Password Flow with JWT tokens for authentication. The architecture follows a layered approach:

1. **Routers Layer** (`app/routers/`) - HTTP endpoints that handle requests/responses
2. **Business Logic Layer** (`app/auth.py`, `app/security.py`) - Authentication logic and JWT handling
3. **Data Layer** (`app/models.py`, `app/database.py`) - SQLModel ORM with SQLite database
4. **Validation Layer** (`app/schemas.py`) - Pydantic models for request/response validation

### OAuth2 Authentication Implementation

#### Authentication Flow
1. **User Registration** (`POST /auth/register`)
   - Accepts: username, email, password, full_name
   - Validates uniqueness of username and email
   - Hashes password using bcrypt with salt rounds
   - Stores user in SQLite database
   - Returns: UserResponse (without password)

2. **User Login** (`POST /auth/token`)
   - Accepts: OAuth2PasswordRequestForm (username, password)
   - Authenticates against hashed password in database
   - Generates JWT token with HS256 algorithm
   - JWT payload contains: `{"sub": username, "exp": expiration_time}`
   - Returns: `{"access_token": jwt_token, "token_type": "bearer"}`

3. **Token Validation**
   - Bearer token extracted from Authorization header
   - JWT signature verified using SECRET_KEY
   - Expiration time checked automatically
   - User fetched from database using username in token
   - Returns 401 if token invalid/expired

4. **Protected Endpoint Access**
   - Use `Depends(get_current_active_user)` for authentication
   - Automatically validates JWT and fetches user object
   - Checks user.is_active flag before granting access

### Key Dependencies and Their Roles
- **SQLModel**: Type-safe ORM that combines SQLAlchemy with Pydantic
- **python-jose[cryptography]**: JWT token creation and validation
- **passlib[bcrypt]**: Password hashing
- **OAuth2PasswordBearer**: FastAPI's OAuth2 implementation for Bearer token authentication

### Database Session Management
- Uses dependency injection via `get_session()` in `database.py`
- Sessions are yielded per request to ensure proper cleanup
- SQLite configured with `check_same_thread=False` for FastAPI compatibility

### Configuration Management
- Settings loaded from environment variables via `pydantic-settings`
- Config cached using `@lru_cache()` decorator
- Defaults provided in `app/config.py`, overridable via `.env` file

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

## OAuth2 Implementation Details

### Core Components

#### 1. Security Module (`app/security.py`)
- **`verify_password(plain_password, hashed_password)`**: Bcrypt password verification
- **`get_password_hash(password)`**: Bcrypt password hashing with salt
- **`create_access_token(data, expires_delta)`**: JWT token generation
- **`decode_token(token)`**: JWT token validation and decoding

#### 2. Authentication Module (`app/auth.py`)
- **`oauth2_scheme`**: OAuth2PasswordBearer instance for token extraction
- **`authenticate_user(session, username, password)`**: User credential verification
- **`get_current_user(token, session)`**: JWT validation and user retrieval
- **`get_current_active_user(current_user)`**: Active user verification
- **`get_current_user_from_cookie(request, session)`**: Cookie-based authentication for UI
- **`get_current_user_optional(user)`**: Optional authentication dependency

#### 3. Configuration (`app/config.py`)
Key environment variables:
- `SECRET_KEY`: JWT signing key (min 32 characters for production)
- `ALGORITHM`: JWT algorithm (default: "HS256")
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime (default: 30)
- `DATABASE_URL`: SQLite connection string

### Authentication Methods

#### 1. Bearer Token Authentication (API)
```python
from app.auth import get_current_active_user

@router.get("/api/protected")
async def api_endpoint(user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {user.username}"}
```

#### 2. Cookie Authentication (Web UI)
```python
from app.auth import get_current_user_from_cookie

@router.get("/dashboard")
async def web_page(user: Optional[User] = Depends(get_current_user_from_cookie)):
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("dashboard.html", {"user": user})
```

#### 3. Optional Authentication
```python
from app.auth import get_current_user_optional

@router.get("/public")
async def mixed_endpoint(user: Optional[User] = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user.username}"}
    return {"message": "Hello anonymous"}
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
from app.auth import get_current_active_user
from app.models import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"user": current_user}
```

### Adding Admin-Only Endpoints
```python
from app.auth import get_current_active_user
from fastapi import HTTPException, status

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
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

### Customizing Token Expiration
```python
from datetime import timedelta

# In your login endpoint
access_token_expires = timedelta(hours=24)  # Custom expiration
access_token = create_access_token(
    data={"sub": user.username},
    expires_delta=access_token_expires
)
```

### Adding Refresh Tokens
To implement refresh tokens:
1. Create a new `refresh_token` field in the Token response model
2. Generate a longer-lived refresh token in the login endpoint
3. Add a `/auth/refresh` endpoint to exchange refresh tokens for new access tokens
4. Store refresh tokens securely (consider Redis or database storage)