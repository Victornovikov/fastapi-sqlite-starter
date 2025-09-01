# FastAPI Authentication Boilerplate

A production-ready FastAPI application with SQLModel ORM, SQLite database, and JWT-based authentication following OAuth2 standards.

## 🚀 Features

- **JWT Authentication** - OAuth2 Password Flow with Bearer tokens
- **SQLModel ORM** - Type-safe database operations with SQLite
- **User Management** - Registration, login, profile management
- **Protected Endpoints** - Role-based access control ready
- **Password Security** - Bcrypt hashing with salt
- **Data Validation** - Pydantic schemas with email validation
- **Auto Documentation** - Interactive Swagger UI and ReDoc
- **Testing Suite** - Comprehensive pytest test coverage
- **Type Safety** - Full type hints throughout the codebase

## 📋 Requirements

- Python 3.8+
- pip package manager

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```

### 5. Generate a secure secret key
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Add the generated key to your `.env` file as `SECRET_KEY`

## 🚀 Running the Application

### Development mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the application is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs` - Interactive API documentation
- **ReDoc**: `http://localhost:8000/redoc` - Alternative API documentation
- **OpenAPI Schema**: `http://localhost:8000/openapi.json` - Raw OpenAPI specification

## 🔌 API Endpoints

### 🔐 Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/token` | Login and get JWT token | No |

### 👤 User Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users/me` | Get current user profile | Yes |
| PUT | `/users/me` | Update current user profile | Yes |
| GET | `/users/` | List all users | Yes (Superuser) |

## 💡 Usage Examples

### 1️⃣ Register a new user
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 2️⃣ Login to get access token
```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=SecurePass123!"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3️⃣ Access protected endpoint
```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4️⃣ Update user profile
```bash
curl -X PUT "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith",
    "email": "john.smith@example.com"
  }'
```

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app initialization
│   ├── database.py      # Database connection and session management
│   ├── models.py        # SQLModel database models
│   ├── schemas.py       # Pydantic validation schemas
│   ├── auth.py          # Authentication dependencies
│   ├── config.py        # Configuration management
│   ├── security.py      # Password hashing and JWT utilities
│   └── routers/
│       ├── __init__.py
│       ├── auth.py      # Authentication endpoints
│       └── users.py     # User management endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Pytest fixtures
│   ├── test_auth.py     # Authentication tests
│   └── test_user_access.py  # User access control tests
├── plans/
│   └── fastapi-auth-implementation.md  # Implementation plan
├── .env.example         # Example environment variables
├── .gitignore          # Git ignore file
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── tests.md           # Testing documentation
```

## 🧪 Testing

The project includes comprehensive test coverage. See [tests.md](tests.md) for detailed testing documentation.

Quick test run:
```bash
pytest tests/ -v
```

## 🔒 Security Considerations

### Required for Production

- **HTTPS Only** - Always use HTTPS in production environments
- **Strong SECRET_KEY** - Generate a cryptographically secure key (min 32 characters)
- **Environment Variables** - Never hardcode secrets in code
- **Rate Limiting** - Implement rate limiting to prevent brute force attacks
- **CORS Configuration** - Configure CORS properly for your frontend domain

### Recommended Enhancements

- **Email Verification** - Verify user emails during registration
- **Password Reset** - Implement secure password reset flow
- **2FA/MFA** - Add two-factor authentication
- **Session Management** - Implement refresh tokens
- **Audit Logging** - Log authentication events
- **Password Policy** - Enforce strong password requirements

## 🚀 Deployment

### Using Docker (Recommended)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```env
DATABASE_URL=sqlite:///./prod.db  # Use PostgreSQL in production
SECRET_KEY=your-production-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- SQLModel for type-safe ORM
- Pydantic for data validation
- All contributors and maintainers