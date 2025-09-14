# Fix Login Flow Plan

## Problem Summary
The login flow is broken with 30+ failing tests related to authentication. The main issues are:
1. LoginManager configuration incompatibility with fastapi-login v1.10.3
2. CSRF token not being properly handled in form submissions
3. Cookie management issues between manager.set_cookie() and response.set_cookie()
4. Token decoding and validation problems

## Root Cause Analysis

### 1. LoginManager Secret Type Mismatch
- **Issue**: `manager.secret` returns `SymmetricSecret` object, not string
- **Location**: `app/login_manager.py:27`, `tests/test_fastapi_login.py:15`
- **Impact**: Test assertion fails, potential token validation issues

### 2. CSRF Token Form Data Issue
- **Issue**: CSRF token sent as form data but not parsed correctly
- **Location**: `app/routers/ui.py:146`
- **Error**: `Field required` for CSRF in POST /auth/login
- **Impact**: All web-based login/signup fails with 422 error

### 3. Cookie Setting Conflicts
- **Issue**: Mixed use of `manager.set_cookie()` and manual `response.set_cookie()`
- **Location**: `app/routers/auth.py:88`, `app/routers/ui.py:193-200`
- **Impact**: Inconsistent cookie behavior, logout issues

### 4. Token Decoding Issues
- **Issue**: `manager.decode_token()` may not work as expected
- **Location**: `app/login_manager.py:108`
- **Impact**: Cookie authentication fails, optional auth doesn't work

## Fix Strategy

### Phase 1: Fix Core LoginManager Issues
1. Update LoginManager configuration test to handle SymmetricSecret type
2. Fix token decoding in get_current_user_optional()
3. Ensure load_user() works correctly

**Test After**: `pytest tests/test_fastapi_login.py::test_login_manager_configuration -v`

### Phase 2: Fix CSRF Token Handling
1. Debug why CSRF token is not being received in form data
2. Check if test client is sending form data correctly
3. Ensure CSRF validation works with form-encoded data

**Test After**: `pytest tests/test_fastapi_login.py::test_web_login_creates_cookie -v`

### Phase 3: Standardize Cookie Management
1. Use only `manager.set_cookie()` for consistency
2. Fix logout to use manager's cookie deletion method
3. Ensure cookie properties are set correctly

**Test After**: `pytest tests/test_fastapi_login.py::test_logout_clears_cookie -v`

### Phase 4: Fix Authentication Flow
1. Fix cookie-based authentication in protected routes
2. Fix header-based authentication
3. Ensure optional authentication works

**Test After**: `pytest tests/test_fastapi_login.py::test_cookie_authentication_works tests/test_fastapi_login.py::test_header_authentication_works -v`

### Phase 5: Fix Remaining UI Routes
1. Update all UI routes to work with fixed authentication
2. Fix remember-me functionality
3. Ensure all HTMX responses work correctly

**Test After**: `pytest tests/test_ui_routes.py tests/test_remember_me.py -v`

## Implementation Details

### Fix 1: LoginManager Configuration Test
```python
# tests/test_fastapi_login.py:15
# Change from:
assert manager.secret == settings.secret_key
# To:
assert str(manager.secret.secret.get_secret_value()) == settings.secret_key
# OR just remove this assertion as it's testing internal implementation
```

### Fix 2: CSRF Form Data Parsing
```python
# Check if form data is being sent correctly
# The issue might be in how TestClient sends multipart/form-data
# Need to ensure content-type is application/x-www-form-urlencoded
```

### Fix 3: Cookie Management
```python
# app/routers/ui.py:193-200
# Replace manual cookie setting with:
manager.set_cookie(response, access_token)
# Remove manual response.set_cookie() calls
```

### Fix 4: Token Decoding
```python
# app/login_manager.py:108
# Check if decode_token returns the payload directly or wrapped
# May need to update to:
payload = manager._get_payload(token)
# or use the built-in validation
```

## Success Criteria
- All tests in `tests/test_fastapi_login.py` pass
- All tests in `tests/test_auth.py` pass
- Web login works via UI
- API login works via /auth/token
- Cookie and header authentication both work
- Remember-me functionality works
- Logout properly clears cookies

## Testing Command Sequence
```bash
# After each fix, run specific test
pytest tests/test_fastapi_login.py::test_name -xvs

# After all fixes, run full test suite
pytest tests/test_fastapi_login.py -v
pytest tests/test_auth.py -v
pytest tests/test_ui_routes.py -v
pytest tests/test_remember_me.py -v

# Final validation
pytest tests/ -v
```

## Notes
- Do NOT add workarounds or hacks
- Fix the root cause, not symptoms
- Maintain compatibility with fastapi-login v1.10.3
- Keep the code clean and maintainable
- Test after each fix to ensure no regression