# FastAPI + SQLite + HTMX Starter Template

A modern, production-ready web application template combining FastAPI backend with HTMX-powered frontend for seamless user interactions.

## Features

### Authentication & Security
- **JWT Cookie Authentication** - Secure httpOnly cookies for web UI
- **API Token Support** - OAuth2-compatible endpoints for API clients
- **User Registration & Login** with secure bcrypt password hashing
- **Password Reset** functionality via email with Resend integration
- **CSRF Protection** using double-submit cookie pattern
- **Role-based Access Control** with admin/superuser support

### Frontend
- **HTMX-Powered UI** for dynamic, SPA-like experience without JavaScript complexity
- **Pico CSS** for clean, modern styling with no build step
- **Template Fragments** for efficient partial page updates
- **Dark/Light Theme** toggle with localStorage persistence
- Pages: Landing, Login/Signup, Dashboard, Profile, Items, Password Reset

### Backend Architecture
- **FastAPI** with async/await support
- **SQLModel ORM** combining SQLAlchemy with Pydantic validation
- **SQLite Database** with automatic table creation
- **Dependency Injection** for clean, testable code
- **Environment-based Configuration** with .env support
- **Optional LLM Integration** with OpenAI API support

### Example CRUD (Items)
- Full CRUD operations with both HTML (HTMX) and JSON API endpoints
- User-scoped data access
- Ready to customize for your use case

### Developer Tools
- Comprehensive test suite with pytest
- Setup script for quick project initialization
- Admin promotion script
- Centralized logging with rotation

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd fastapi-sqlite-starter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run setup script (creates .env, initializes database)
python scripts/setup.py
```

### 2. Configure Environment

Edit `.env` file with your settings:

```env
SECRET_KEY=your-secure-secret-key-here
DATABASE_URL=sqlite:///./app.db
ENVIRONMENT=development

# For password reset emails (optional)
RESEND_API_KEY=re_xxx_your_key
EMAIL_FROM=noreply@yourdomain.com

# For LLM features (optional)
OPENAI_API_KEY=sk-xxx_your_key
```

### 3. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000

## Project Structure

```
├── app/
│   ├── routers/           # API and UI routes
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── users.py       # User management
│   │   ├── items.py       # Example CRUD router
│   │   └── ui.py          # HTMX UI routes
│   ├── templates/         # Jinja2 templates
│   │   ├── fragments/     # HTMX partial templates
│   │   └── *.html         # Page templates
│   ├── config.py          # Settings from environment
│   ├── models.py          # SQLModel database models
│   ├── schemas.py         # Pydantic validation schemas
│   ├── database.py        # Database configuration
│   ├── security.py        # CSRF and security utilities
│   ├── login_manager.py   # JWT authentication
│   ├── email_client.py    # Resend email integration
│   ├── llm_service.py     # OpenAI/LLM integration
│   ├── logging_config.py  # Centralized logging
│   └── main.py            # FastAPI application
├── scripts/
│   ├── setup.py           # Project setup script
│   ├── promote_to_admin.py # Admin promotion script
│   └── list_admins.py     # List admin users
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── README.md
```

## API Endpoints

### Public Endpoints
- `GET /` - Landing page
- `GET /login` - Login/signup page
- `POST /auth/register` - API user registration
- `POST /auth/token` - API login (returns JWT)
- `POST /auth/login` - Web UI login (sets cookie)
- `POST /auth/signup` - Web UI registration
- `POST /auth/forgot` - Request password reset
- `POST /auth/reset` - Reset password with token

### Protected Endpoints
- `GET /dashboard` - User dashboard
- `GET /profile` - User profile settings
- `GET /items` - Items list page
- `POST /items/add` - Create item (HTMX)
- `DELETE /items/{id}` - Delete item (HTMX)
- `GET /api/items` - Items JSON API
- `POST /api/items` - Create item JSON API
- `GET /users/me` - Get current user
- `POST /users/update-profile` - Update profile (HTMX)

### Admin Endpoints
- `GET /users/` - List all users (admin only)

## Customization

### Adding a New Model

1. Define model in `app/models.py`:
```python
class YourModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    # ... your fields
```

2. Add schemas in `app/schemas.py`
3. Create router in `app/routers/yourmodel.py` (copy items.py as template)
4. Register router in `app/main.py`
5. Create templates as needed

### Using the LLM Service

```python
from app.llm_service import get_llm_service

llm = get_llm_service()
if llm:
    response = await llm.chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ])
    
    # Or for JSON responses:
    data = await llm.complete_json(
        "Return a JSON object with name and age fields",
        system_prompt="You are a data generator."
    )
```

### HTMX Form Pattern

```html
<form hx-post="/your/endpoint" 
      hx-target="#result" 
      hx-swap="innerHTML">
    <input type="hidden" name="csrf" value="{{ csrf_token }}">
    <input type="text" name="field" required>
    <button type="submit">Submit</button>
</form>
<div id="result"></div>
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Scripts

### Setup Script
```bash
# Interactive setup
python scripts/setup.py

# Non-interactive (for CI/CD)
python scripts/setup.py --no-interactive
```

### Promote User to Admin
```bash
python scripts/promote_to_admin.py admin@example.com
```

## Production Deployment

1. Set strong `SECRET_KEY` in environment
2. Set `ENVIRONMENT=production`
3. Enable HTTPS
4. Consider PostgreSQL for production database
5. Set proper CORS origins in `app/main.py`

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Database | SQLite + SQLModel |
| Auth | JWT + bcrypt |
| Frontend | Jinja2 + HTMX |
| Styling | Pico CSS |
| Email | Resend |
| LLM | OpenAI (optional) |

## License

MIT License - Feel free to use this template for your projects!
