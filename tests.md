# Testing Documentation

## 📋 Overview

This project uses **pytest** as the testing framework with comprehensive test coverage for authentication, user management, and access control features.

## 🚀 Quick Start

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py -v
```

### Run specific test
```bash
pytest tests/test_auth.py::test_register_user -v
```

## 📦 Test Dependencies

The following packages are required for testing (included in `requirements.txt`):

- `pytest==7.4.4` - Testing framework
- `httpx==0.26.0` - Async HTTP client for testing FastAPI
- `email-validator==2.2.0` - Email validation for Pydantic schemas

### Installing test dependencies
```bash
pip install -r requirements.txt
```

## 🏗️ Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Shared fixtures and configuration
├── test_auth.py             # Authentication tests
└── test_user_access.py      # User access control tests
```

## 🔧 Test Configuration

### conftest.py - Shared Fixtures

The `conftest.py` file provides:

1. **`session` fixture**: Creates an in-memory SQLite database for each test
2. **`client` fixture**: Provides a TestClient with database dependency injection

```python
@pytest.fixture(name="session")
def session_fixture():
    # Creates in-memory database for testing
    
@pytest.fixture(name="client")
def client_fixture(session: Session):
    # Provides test client with mocked database
```

## 📝 Test Suites

### 1. Authentication Tests (`test_auth.py`)

Tests core authentication functionality:

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_register_user` | Register a new user | User created successfully |
| `test_register_duplicate_username` | Attempt duplicate username | Returns 400 error |
| `test_register_duplicate_email` | Attempt duplicate email | Returns 400 error |
| `test_login_success` | Login with valid credentials | Returns JWT token |
| `test_login_wrong_password` | Login with wrong password | Returns 401 error |
| `test_login_nonexistent_user` | Login with non-existent user | Returns 401 error |

### 2. User Access Control Tests (`test_user_access.py`)

Tests user isolation and access control:

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_users_can_access_own_profile` | Users access their own profiles | Each user sees only their data |
| `test_users_cannot_access_without_token` | Access without authentication | Returns 401 error |
| `test_users_cannot_access_with_invalid_token` | Access with invalid token | Returns 401 error |
| `test_users_can_update_own_profile` | Users update their profiles | Updates only their own data |
| `test_user_tokens_are_unique` | Each user gets unique token | Tokens are different |
| `test_regular_users_cannot_list_all_users` | Non-admin tries to list users | Returns 403 error |
| `test_email_update_conflict` | Update email to existing one | Returns 400 error |

## 🧪 Running Tests

### Basic test run
```bash
pytest tests/ -v
```

### With output capture disabled (see print statements)
```bash
pytest tests/ -v -s
```

### Run tests in parallel (faster)
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

### Run with warnings displayed
```bash
pytest tests/ -v -W default
```

### Generate HTML coverage report
```bash
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Generate terminal coverage report
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## 🎯 Test Coverage Goals

Current test coverage includes:

- ✅ User registration
- ✅ User authentication (login)
- ✅ JWT token generation
- ✅ Protected endpoint access
- ✅ User profile retrieval
- ✅ User profile updates
- ✅ Access control (user isolation)
- ✅ Error handling

### Future test additions recommended:

- ⏳ Token expiration handling
- ⏳ Password reset flow
- ⏳ Email verification
- ⏳ Rate limiting
- ⏳ CORS configuration
- ⏳ Database migrations
- ⏳ Performance testing

## 🐛 Debugging Tests

### Run specific test with verbose output
```bash
pytest tests/test_auth.py::test_register_user -vv
```

### Use Python debugger (pdb)
```python
def test_something():
    import pdb; pdb.set_trace()
    # Test code here
```

### Print SQL queries during tests
Set `echo=True` in the test database engine configuration.

### Check test database state
```python
def test_check_db(session: Session):
    users = session.exec(select(User)).all()
    print(f"Users in DB: {users}")
```

## 📊 Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest tests/ -v --cov=app
```

## 🔍 Common Test Scenarios

### Testing authenticated endpoints
```python
def test_protected_endpoint(client: TestClient):
    # Register and login
    client.post("/auth/register", json={...})
    response = client.post("/auth/token", data={...})
    token = response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### Testing error cases
```python
def test_invalid_input(client: TestClient):
    response = client.post("/auth/register", json={
        "username": "",  # Invalid
        "email": "not-an-email",  # Invalid
        "password": "123"  # Too short
    })
    assert response.status_code == 422  # Validation error
```

### Testing database state
```python
def test_database_state(client: TestClient, session: Session):
    # Perform action
    client.post("/auth/register", json={...})
    
    # Check database
    user = session.exec(select(User)).first()
    assert user is not None
    assert user.username == "expected_username"
```

## ⚠️ Important Notes

1. **Test Isolation**: Each test runs with a fresh in-memory database
2. **No Side Effects**: Tests don't affect the production database
3. **Fast Execution**: In-memory SQLite makes tests run quickly
4. **Deterministic**: Tests should always produce the same results

## 🆘 Troubleshooting

### Issue: Import errors
**Solution**: Ensure you're in the project root directory and virtual environment is activated

### Issue: Database connection errors
**Solution**: Tests use in-memory SQLite, no external database needed

### Issue: Slow tests
**Solution**: Use pytest-xdist for parallel execution: `pytest -n auto`

### Issue: Tests pass locally but fail in CI
**Solution**: Check for:
- Environment variable differences
- Python version compatibility
- Missing dependencies in requirements.txt
- File path issues (use absolute paths)

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/testing/)
- [HTTPX Documentation](https://www.python-httpx.org/)