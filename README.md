# FastAPI + SQLite + HTMX + Resend Template

A modern, production-ready web application template combining FastAPI backend with HTMX-powered frontend for seamless user interactions.

## 🚀 Features

### Authentication & Security
- **JWT Cookie Authentication** - Secure httpOnly cookies for web UI
- **API Token Support** - OAuth2-compatible endpoints for API clients
- **User Registration & Login** with secure bcrypt password hashing
- **Password Reset** functionality via email with Resend integration
- **CSRF Protection** using double-submit cookie pattern
- **Role-based Access Control** with admin/superuser support

### Frontend
- **HTMX-Powered UI** for dynamic, SPA-like experience
- **Responsive Forms** with real-time validation and error handling
- **Pico CSS** for clean, modern styling
- **Template Fragments** for efficient partial page updates
- Pages: Login/Signup, Dashboard, Profile, Password Reset (forgot/reset)

### Backend Architecture
- **FastAPI** with async/await support
- **SQLModel ORM** combining SQLAlchemy with Pydantic validation
- **SQLite Database** with automatic table creation
- **Dependency Injection** for clean, testable code
- **Environment-based Configuration** with .env support

### Testing
- Comprehensive test suite with pytest
- In-memory database for isolated testing
- CSRF protection tests
- Authentication flow tests
- Password reset tests
- Admin access tests

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd fastapi-sqlite-htmx-resend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add the generated key to .env as SECRET_KEY
```

## 🔧 Configuration

Edit `.env` file:

```env
SECRET_KEY=your-secure-secret-key-here
DATABASE_URL=sqlite:///./app.db
ENVIRONMENT=development
ACCESS_TOKEN_EXPIRE_MINUTES=30

# For password reset emails
RESEND_API_KEY=re_xxx_change_this
EMAIL_FROM=Your App <noreply@yourdomain.com>
EMAIL_FROM_NAME=Your App Name
RESET_URL_BASE=https://yourdomain.com/reset

# Optional: Webhook verification
RESEND_WEBHOOK_SECRET=whsec_xxx_change_this
```

## 🏃 Running the Application

### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Visit: http://localhost:8000

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_login -v
```

## 📁 Project Structure

```
├── app/
│   ├── routers/        # API and UI routes
│   │   ├── auth.py     # Authentication endpoints
│   │   ├── users.py    # User management
│   │   └── ui.py       # HTMX UI routes
│   ├── templates/      # Jinja2 templates
│   │   ├── fragments/  # HTMX partial templates
│   │   └── *.html      # Page templates
│   ├── auth.py         # Authentication logic
│   ├── security.py     # Security utilities
│   ├── models.py       # SQLModel database models
│   ├── schemas.py      # Pydantic validation schemas
│   ├── database.py     # Database configuration
│   └── main.py         # FastAPI application
├── tests/              # Test suite
├── requirements.txt    # Python dependencies
└── .env.example       # Environment variables template
```

## 🔑 API Endpoints

### Public Endpoints
- `POST /auth/register` - API user registration
- `POST /auth/token` - API login (returns JWT for Bearer auth)
- `POST /auth/login` - Web UI login (sets httpOnly JWT cookie)
- `POST /auth/signup` - Web UI registration (sets httpOnly JWT cookie)
- `POST /auth/forgot` - Request password reset
- `POST /auth/reset` - Reset password with token
- `POST /logout` - Clear authentication cookie

### Protected Endpoints
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `GET /users/` - List all users (admin only)

### UI Routes
- `/` - Landing page
- `/login` - Login/Signup page
- `/dashboard` - User dashboard (protected)
- `/profile` - User profile (protected)
- `/forgot` - Password reset request
- `/reset` - Password reset form

## 🛠️ Development Tips

### Adding Protected Endpoints
```python
from app.auth import get_current_active_user

@router.get("/protected")
async def protected_route(user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {user.username}"}
```

### Authentication Methods

The template supports dual authentication methods:

1. **Web UI (Cookie-based)**: JWT stored in secure httpOnly cookies with CSRF protection
2. **API (Token-based)**: JWT returned as Bearer token for API clients (OAuth2-compatible)

### Using HTMX Fragments
```python
@router.post("/auth/login", response_class=HTMLResponse)
async def handle_login(request: Request, email: str = Form(...),
                      password: str = Form(...), csrf: str = Form(...)):
    # Verify CSRF, authenticate user
    verify_csrf(request, csrf)
    user = authenticate_user(session, email, password)

    if user:
        # Create JWT and set cookie with HTMX redirect
        response = hx_redirect("/dashboard", request)
        response.set_cookie("access_token", token, httponly=True,
                          secure=settings.cookie_secure, samesite="lax")
        return response

    return templates.TemplateResponse("fragments/auth_error.html",
                                    {"error": "Invalid credentials"})
```

## 📝 License

MIT License - Feel free to use this template for your projects!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.