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

### Authentication Flow
1. User registers via `/auth/register` with username, email, password
2. Password is hashed using bcrypt before storage
3. User logs in via `/auth/token` (OAuth2 standard endpoint) receiving a JWT
4. JWT contains username in the `sub` claim with expiration time
5. Protected endpoints use `Depends(get_current_active_user)` to validate JWT and fetch user

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

### Public Endpoints
- `POST /auth/register` - User registration
- `POST /auth/token` - OAuth2 login endpoint

### Protected Endpoints
- `GET /users/me` - Requires valid JWT
- `PUT /users/me` - Requires valid JWT
- `GET /users/` - Requires valid JWT + superuser flag

## Common Development Tasks

### Adding New Protected Endpoints
Use the `get_current_active_user` dependency:
```python
from app.auth import get_current_active_user

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"user": current_user}
```

### Modifying User Model
1. Update `app/models.py` with new fields
2. Update `app/schemas.py` with corresponding Pydantic schemas
3. Consider database migration strategy (currently recreates tables on startup)

### Adding New Authentication Methods
Extend `app/auth.py` and `app/security.py` while maintaining OAuth2 compatibility for existing endpoints.