# Testing Documentation

## 📋 Overview

This project uses **pytest** as the testing framework with comprehensive test coverage for authentication, user management, and access control features.

### Test Suite Optimization Results

- **Before**: 86 tests across 11 files (2,405 lines)
- **After**: 78 tests across 9 files (~1,900 lines)
- **Reduction**: 10% fewer tests, 20% less code
- **Improvements**:
  - Heavy use of parametrization for similar scenarios
  - Consolidated overlapping login/auth tests
  - Merged password reset unit & integration tests
  - No loss of security coverage

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
├── __init__.py                    # Test package marker
├── conftest.py                    # Shared fixtures and configuration
├── test_auth.py                   # Consolidated authentication & login tests
├── test_user_access.py            # User access control & isolation tests
├── test_admin_access.py           # Admin privileges and user management
├── test_password_reset.py         # Complete password reset flow tests
├── test_ui_routes.py              # UI rendering and form submission tests
├── test_csrf_protection.py        # CSRF token validation tests
├── test_remember_me.py            # Remember-me functionality tests
├── test_error_handling.py         # Error response and rate limiting tests
└── test_email.py                  # Email service tests
```

### Test Organization (Optimized)

**Total: ~78 tests** (reduced from 86 through consolidation)

| File | Tests | Purpose |
|------|-------|---------|
| `test_auth.py` | ~20 | Registration, login, tokens, logout |
| `test_ui_routes.py` | ~10 | Parametrized UI rendering & forms |
| `test_password_reset.py` | ~8 | Complete reset flow with parametrized edge cases |
| `test_user_access.py` | 7 | User isolation & data protection |
| `test_admin_access.py` | 6 | Admin privileges |
| `test_remember_me.py` | 6 | Extended session functionality |
| `test_csrf_protection.py` | 5 | CSRF security |
| `test_error_handling.py` | ~12 | Error responses & rate limits |
| `test_email.py` | 5 | Email service mocking |

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

## 🎯 Parametrized Testing

### What are Parametrized Tests?

Parametrized tests allow running the same test function with different input values, reducing code duplication while maintaining comprehensive coverage.

### Example: UI Page Rendering

**Before (3 separate tests, 30+ lines):**
```python
def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign In" in response.text

def test_signup_page_renders(client):
    response = client.get("/signup")
    assert response.status_code == 200
    assert "Create Account" in response.text

def test_forgot_page_renders(client):
    response = client.get("/forgot")
    assert response.status_code == 200
    assert "Reset Password" in response.text
```

**After (1 parametrized test, 10 lines):**
```python
@pytest.mark.parametrize("path,expected_text", [
    ("/login", "Sign In"),
    ("/signup", "Create Account"),
    ("/forgot", "Reset Password"),
])
def test_public_pages_render(client, path, expected_text):
    response = client.get(path)
    assert response.status_code == 200
    assert expected_text in response.text
```

### Benefits
- **50-70% less code** for similar test scenarios
- **Easier maintenance** - fix bugs in one place
- **Better coverage** - easy to add edge cases
- **Clear test output** - pytest shows each parameter set as a separate test

## 📝 Test Suites

### 1. Authentication Tests (`test_auth.py`) - Consolidated

Comprehensive authentication testing with ~20 tests covering:

**Registration:**
- ✅ Successful user registration
- ✅ Duplicate email prevention

**Login (Parametrized):**
- ✅ API endpoint (`/auth/token`) and Web endpoint (`/auth/login`)
- ✅ Cookie and header authentication
- ✅ Wrong password, non-existent user, inactive user

**Token Management:**
- ✅ JWT token creation and validation
- ✅ Expired token rejection
- ✅ Invalid token rejection
- ✅ Cookie vs header authentication

**Session Management:**
- ✅ Logout clears cookies
- ✅ Protected endpoint access
- ✅ Optional authentication endpoints

### 2. Password Reset Tests (`test_password_reset.py`) - Consolidated

Complete password reset flow with parametrized edge cases:

**Core Flow:**
- ✅ Forgot password page rendering
- ✅ Token creation on reset request
- ✅ Complete reset flow from request to new password

**Security Tests (Parametrized):**
- ✅ Expired tokens rejected
- ✅ Used tokens rejected
- ✅ Invalid tokens rejected
- ✅ Non-existent user handling (no information leak)

### 3. UI Routes Tests (`test_ui_routes.py`) - Parametrized

Optimized UI testing with heavy use of parametrization:

**Page Rendering (Parametrized):**
- ✅ Public pages: `/`, `/login`, `/signup`, `/forgot`
- ✅ Protected pages require authentication
- ✅ Auth pages redirect when logged in

**Form Submissions:**
- ✅ HTMX vs standard request handling
- ✅ CSRF token validation
- ✅ Error responses as HTML fragments

### 4. User Access Control Tests (`test_user_access.py`)

Critical security tests for user isolation:

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

## 🔥 Critical Lessons Learned - MUST READ

### 1. Cookie Contamination in Tests
**Problem**: Using a single TestClient instance for multiple users causes cookie contamination - Bob's login overwrites Alice's cookie, making Alice's requests return Bob's data.

**Solution**: Each user must have their own TestClient instance to simulate separate browser sessions:
```python
# ❌ WRONG - Causes security test failures
def test_multiple_users(client: TestClient):
    alice_token = login_user(client, "alice")
    bob_token = login_user(client, "bob")  # Bob's cookie overwrites Alice's!

# ✅ CORRECT - Separate clients for each user
def test_multiple_users(client: TestClient):
    alice_client = TestClient(client.app)
    bob_client = TestClient(client.app)
    alice_token = login_user(alice_client, "alice")
    bob_token = login_user(bob_client, "bob")
```

### 2. Database Engine Override in Tests
**Problem**: The `load_user()` function imports engine directly, missing test overrides.

**Solution**: Import the module and access engine through it:
```python
# ❌ WRONG - Won't see test database override
from app.database import engine
db = Session(engine)

# ✅ CORRECT - Respects test database override
import app.database
db = Session(app.database.engine)
```

### 3. Async/Await with Rate Limit Handlers
**Problem**: `_rate_limit_exceeded_handler` returns JSONResponse (not awaitable) but code tries to await it.

**Solution**: Don't await synchronous functions:
```python
# ❌ WRONG
return await _rate_limit_exceeded_handler(request, exc)

# ✅ CORRECT
return _rate_limit_exceeded_handler(request, exc)
```

### 4. Timezone-Aware Datetime Handling
**Problem**: SQLite stores datetime without timezone, causing comparison errors between naive and aware datetimes.

**Solution**:
- Use `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`
- In tests, compare as naive when retrieving from SQLite:
```python
# ✅ CORRECT for SQLite tests
assert reset_token.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
```

### 5. Rate Limiting in Tests
**Problem**: Tests fail when they exceed rate limits (e.g., registering 10 users with 5/minute limit).

**Solution**: Stay under rate limits or reset rate limiter between test runs:
```python
# In conftest.py
if hasattr(app.state, 'limiter'):
    app.state.limiter.reset()
```

### 6. CSRF Token Naming Consistency
**Problem**: Inconsistent CSRF cookie names ("csrf" vs "csrftoken") between app and tests.

**Solution**: Use consistent naming throughout:
```python
CSRF_COOKIE_NAME = "csrftoken"  # Use everywhere
```

### 7. HTML vs JSON Response for UI Rate Limits
**Problem**: UI endpoints expect HTML responses but rate limiter returns JSON.

**Solution**: Check request path and return appropriate format:
```python
if request.url.path.startswith("/auth/"):
    return HTMLResponse(content="<html>...</html>", status_code=429)
else:
    return _rate_limit_exceeded_handler(request, exc)  # JSON
```

### 8. Import Path Consistency
**Problem**: `verify_password` moved between modules causing import errors.

**Solution**: Keep authentication functions in one place (`app.login_manager`) and import consistently.

## ✅ Testing Best Practices

### Before Writing Tests
1. **Run existing tests first** - Ensure all tests pass before adding new ones
2. **Check rate limits** - Know the limits (5/min for registration, 10/min for login)
3. **Use unique test data** - Add UUIDs to emails to avoid conflicts between tests

### When Writing Tests
1. **One user = One client** - Never share TestClient between different users
2. **Clear state between tests** - Reset rate limiters, clear cookies when needed
3. **Use timezone-aware datetimes** - Always use `datetime.now(timezone.utc)`
4. **Test both success AND failure paths** - Include edge cases and error conditions
5. **Keep tests independent** - Each test should work in isolation

### Common Patterns
```python
# Testing multiple users correctly
def test_user_isolation(client: TestClient):
    from fastapi.testclient import TestClient

    # Each user gets their own client
    alice_client = TestClient(client.app)
    bob_client = TestClient(client.app)

    # Register users (using shared client is OK for registration)
    client.post("/auth/register", json=alice_data)
    client.post("/auth/register", json=bob_data)

    # Login with separate clients (maintains separate cookies)
    alice_client.post("/auth/token", data=alice_login)
    bob_client.post("/auth/token", data=bob_login)

    # Each client maintains its own session
    alice_resp = alice_client.get("/users/me")
    bob_resp = bob_client.get("/users/me")
```

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