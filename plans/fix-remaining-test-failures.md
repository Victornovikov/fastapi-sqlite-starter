# Fix Remaining Test Failures Plan

## Current Status
- **27 tests failing** after fixing core login functionality
- Core auth tests (`test_auth.py`) and fastapi-login tests (`test_fastapi_login.py`) are passing
- Issues are mainly in UI routes, remember-me, error handling, and user access tests

## Root Cause Analysis

### 1. CSRF Cookie Name Inconsistency
**Problem**: 
- App uses `"csrftoken"` as cookie name (defined in `app/security.py:15`)
- Many tests expect `"csrf"` as cookie name
- This causes assertion failures when tests check for CSRF cookie

**Affected Files**:
```
tests/test_ui_routes.py - lines 20, 22 (and form field references)
tests/test_remember_me.py - lines 26, 37, 67, 104, 136, 173
tests/test_error_handling.py - lines 57, 68, 91
```

**Solution Strategy**:
- Update all test files to use `"csrftoken"` consistently
- Also update form field references from `f"csrf={csrf_token}"` to `f"csrftoken={csrf_token}"`
- Verify against working tests (`test_csrf_protection.py` already uses `"csrftoken"`)

### 2. Remember-Me Functionality Broken
**Problem**:
- Changed from manual `response.set_cookie()` to `manager.set_cookie()`
- `manager.set_cookie()` doesn't accept `max_age` parameter
- Remember-me needs 30-day expiry, standard needs 30-minute expiry
- Currently all cookies get same expiry regardless of remember-me setting

**Current Code** (`app/routers/ui.py:193`):
```python
manager.set_cookie(response, access_token)  # Ignores custom expiry!
```

**Required Behavior**:
- If remember_me="true": Set cookie with 30-day max_age
- If remember_me=None/false: Set cookie with 30-minute max_age
- Token expiry and cookie max_age must match

**Solution Strategy**:
```python
# Create token with appropriate expiry
if remember_me == "true":
    expires = timedelta(days=30)
else:
    expires = timedelta(minutes=settings.access_token_expire_minutes)

access_token = manager.create_access_token(
    data={"sub": user.email},
    expires=expires
)

# Set cookie with matching max_age
if remember_me == "true":
    # Manual cookie setting for custom expiry
    response.set_cookie(
        key=manager.cookie_name,
        value=access_token,
        max_age=int(expires.total_seconds()),
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax"
    )
else:
    # For standard expiry, we can use manager OR manual
    # Using manual for consistency:
    response.set_cookie(
        key=manager.cookie_name,
        value=access_token,
        max_age=int(expires.total_seconds()),
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax"
    )
```

**Files to Update**:
- `app/routers/ui.py` - `/auth/login` endpoint (line 193)
- `app/routers/ui.py` - `/auth/signup` endpoint (line 267)

### 3. Error Message Inconsistencies
**Problem**:
- fastapi-login library returns `"Invalid credentials"`
- Tests expect `"Invalid authentication credentials"`
- This is a library constant we cannot change

**Affected Tests**:
```
tests/test_error_handling.py:32 - test_401_unauthorized_json_for_api
tests/test_error_handling.py:132 - test_invalid_token_format_error
tests/test_error_handling.py:158 - test_expired_token_error_message
```

**Solution Strategy**:
- Update test assertions to match actual library messages
- Change `"Invalid authentication credentials"` to `"Invalid credentials"`

### 4. User Access Control Test Failures
**Problem**:
- All 6 tests in `test_user_access.py` failing
- Likely due to authentication flow changes and database session handling

**Potential Issues**:
1. Tests might be creating users in one session but authentication uses another
2. The `conftest.py` engine override might not be working for all scenarios
3. Token validation might be failing due to the `get_current_user_optional` fix

**Investigation Needed**:
- Check if users are being created properly in test database
- Verify token generation and validation in test context
- Ensure database session consistency

## Implementation Order

### Phase 1: CSRF Cookie Name Fix
1. Update `tests/test_ui_routes.py`:
   - Line 20: `assert "csrf" in response.cookies` → `assert "csrftoken" in response.cookies`
   - Line 26, 67: `csrf_token = login_page.cookies.get("csrf")` → `csrf_token = login_page.cookies.get("csrftoken")`
   - Line 37, 68, etc: `headers={"Cookie": f"csrf={csrf_token}"}` → `headers={"Cookie": f"csrftoken={csrf_token}"}`

2. Update `tests/test_remember_me.py`:
   - Same pattern as above for all occurrences

3. Update `tests/test_error_handling.py`:
   - Same pattern as above for all occurrences

**Test Command**: 
```bash
pytest tests/test_ui_routes.py::test_login_page_renders -xvs
pytest tests/test_csrf_protection.py -v  # Should still pass
```

### Phase 2: Fix Remember-Me Functionality
1. Update `app/routers/ui.py` `/auth/login` endpoint:
   - Replace `manager.set_cookie()` with manual cookie setting
   - Ensure max_age matches token expiry

2. Update `app/routers/ui.py` `/auth/signup` endpoint:
   - Apply same fix (standard expiry only)

**Test Command**:
```bash
pytest tests/test_remember_me.py -v
pytest tests/test_fastapi_login.py -v  # Should still pass
```

### Phase 3: Fix Error Messages
1. Update `tests/test_error_handling.py`:
   - Replace all occurrences of `"Invalid authentication credentials"` with `"Invalid credentials"`

**Test Command**:
```bash
pytest tests/test_error_handling.py::test_401_unauthorized_json_for_api -xvs
pytest tests/test_error_handling.py::test_invalid_token_format_error -xvs
```

### Phase 4: Fix User Access Control
1. Investigate actual failure reasons
2. Check if it's related to:
   - Database session handling in tests
   - Token generation/validation
   - The `get_current_user_optional` fix

**Test Command**:
```bash
pytest tests/test_user_access.py::TestUserAccessControl::test_users_can_access_own_profile -xvs
```

## Validation Strategy

After each phase:
1. Run the specific tests being fixed
2. Run previously passing tests to ensure no regression:
   ```bash
   pytest tests/test_auth.py -v
   pytest tests/test_fastapi_login.py -v
   ```
3. Check overall test count:
   ```bash
   pytest tests/ --co -q | grep -c "test session"
   ```

## Success Criteria
- All 86 tests passing
- No regression in previously fixed tests
- Remember-me functionality works with 30-day expiry
- Standard login works with 30-minute expiry
- CSRF protection remains functional
- Error messages are consistent

## Risk Mitigation
- Test after each change to catch regressions early
- Keep changes minimal and focused
- Don't modify working code unless necessary
- Preserve the fixes from `test_fastapi_login.py`