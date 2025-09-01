# FastAPI Authentication App with Web UI

A production-ready FastAPI application featuring JWT authentication, SQLModel ORM, and a modern web interface built with HTMX and Pico CSS.

## ✨ Features

### Backend
- **JWT Authentication** - OAuth2 Password Flow with secure httpOnly cookies
- **SQLModel ORM** - Type-safe database operations with SQLite
- **User Management** - Registration, login, profile management
- **Role-Based Access** - Superuser support for admin functionality
- **Security** - Bcrypt password hashing, secure token handling

### Frontend
- **Modern UI** - Clean, responsive design with Pico CSS
- **Dynamic Interactions** - HTMX for seamless page updates
- **Theme Support** - Light/dark mode with persistence
- **Form Validation** - Client and server-side validation
- **Error Handling** - Custom error pages and user feedback

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation
```bash
# Clone repository
git clone <repository-url>
cd fastapi-sqlite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Generate SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Running the Application
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the application at `http://localhost:8000`

## 📚 Documentation

- **Web UI**: `http://localhost:8000` - User interface
- **API Docs**: `http://localhost:8000/docs` - Swagger UI
- **ReDoc**: `http://localhost:8000/redoc` - Alternative API docs

## 🔌 Endpoints

### Web UI Routes
- `/` - Landing page
- `/login` - Login/Signup page
- `/dashboard` - User dashboard (protected)
- `/profile` - User profile (protected)

### API Endpoints
- `POST /auth/register` - User registration → [`app/routers/auth.py`](app/routers/auth.py#L16)
- `POST /auth/token` - Login (OAuth2) → [`app/routers/auth.py`](app/routers/auth.py#L49)
- `GET /users/me` - Current user → [`app/routers/users.py`](app/routers/users.py#L13)
- `PUT /users/me` - Update profile → [`app/routers/users.py`](app/routers/users.py#L18)

## 📁 Project Structure

```
app/
├── templates/          # Jinja2 templates
│   ├── base.html      # Base template with navigation
│   ├── auth.html      # Login/signup forms
│   ├── dashboard.html # User dashboard
│   └── fragments/     # HTMX partial templates
├── routers/
│   ├── auth.py        # Authentication endpoints
│   ├── users.py       # User management endpoints
│   └── ui.py          # Web UI routes
├── main.py            # FastAPI app initialization
├── auth.py            # Authentication logic
├── security.py        # JWT and password utilities
├── models.py          # SQLModel database models
└── schemas.py         # Pydantic validation schemas
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL databases with Python objects
- **Pydantic** - Data validation using Python type hints
- **python-jose** - JWT token handling
- **passlib** - Password hashing

### Frontend
- **Jinja2** - Template engine
- **HTMX** - Dynamic HTML without JavaScript
- **Pico CSS** - Minimal CSS framework
- **jinja2-fragments** - Partial template rendering

### Development
- **pytest** - Testing framework
- **httpx** - Async HTTP client for tests
- **uvicorn** - ASGI server

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

See [`tests/`](tests/) for test implementations and [`tests.md`](tests.md) for testing documentation.

## 🔒 Security

### Production Checklist
- [ ] Use HTTPS only
- [ ] Set strong `SECRET_KEY` (32+ characters)
- [ ] Configure proper CORS origins
- [ ] Enable secure cookies (`secure=True`)
- [ ] Implement rate limiting
- [ ] Use PostgreSQL instead of SQLite

### Authentication Flow
1. User registers/logs in via UI or API
2. Server issues JWT token
3. Token stored in httpOnly cookie (UI) or returned as JSON (API)
4. Subsequent requests include token automatically (UI) or in Authorization header (API)

See [`app/auth.py`](app/auth.py) for implementation details.

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📦 Admin Features

Create admin users:
```bash
python scripts/promote_to_admin.py <username>
```

See [`scripts/`](scripts/) for admin utilities.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.