# HTMX Authentication Best Practices Migration Plan

## Executive Summary

This document outlines a comprehensive migration plan to align our current FastAPI + SQLite + HTMX authentication implementation with industry best practices, specifically optimized for HTMX's cookie-based approach.

## Current State vs Target State Analysis

### Current Implementation Strengths
- ✅ JWT tokens stored in HttpOnly cookies
- ✅ Password hashing with bcrypt
- ✅ Basic HTMX form integration
- ✅ SQLModel ORM with SQLite
- ✅ Separate UI and API authentication paths

### Critical Gaps Identified
- ❌ No CSRF protection
- ❌ Missing password reset functionality
- ❌ Suboptimal HTMX redirect handling
- ❌ Hard-coded security settings
- ❌ No token revocation mechanism
- ❌ Username-based auth instead of email

## Migration Phases

### Phase 1: CSRF Protection Implementation
**Priority: CRITICAL - Security Vulnerability**

#### Step 1.1: Add CSRF Token Generation Functions
**File**: `app/security.py`
```python
def generate_csrf_token() -> str:
    return secrets.token_urlsafe(16)

def set_csrf_cookie(response: Response, token: str):
    response.set_cookie(
        key="csrftoken",
        value=token,
        httponly=False,  # Must be readable by forms
        samesite="lax",
        secure=get_cookie_secure_flag(),
        path="/",
        max_age=3600
    )
```
**Motivation**: CSRF tokens prevent malicious websites from submitting forms on behalf of authenticated users. The double-submit cookie pattern (cookie + hidden field) is HTMX-friendly and doesn't require server-side session storage.

#### Step 1.2: Add CSRF Verification
**File**: `app/security.py`
```python
def verify_csrf(request: Request, form_token: str):
    cookie_token = request.cookies.get("csrftoken")
    if not cookie_token or not form_token or cookie_token != form_token:
        raise HTTPException(status_code=403, detail="CSRF verification failed")
```
**Motivation**: Double-submit validation ensures the request originated from our own forms, not a malicious site.

#### Step 1.3: Update All Form Routes to Set CSRF Cookies
**Files**: `app/routers/ui.py`
- Modify login_page, signup_page to generate and set CSRF cookies
- Pass CSRF token to template context
**Motivation**: Each form needs a fresh CSRF token to prevent replay attacks.

#### Step 1.4: Update Templates with CSRF Hidden Fields
**Files**: `app/templates/auth.html`, all form templates
```html
<input type="hidden" name="csrf" value="{{ csrf }}">
```
**Motivation**: The hidden field completes the double-submit pattern, sending the token back with form data.

#### Step 1.5: Add CSRF Validation to All POST Endpoints
**Files**: `app/routers/ui.py`, `app/routers/auth.py`
- Add `csrf: str = Form(...)` parameter
- Call `verify_csrf(request, csrf)` at start of each handler
**Motivation**: Server-side validation is the actual security enforcement point.

### Phase 2: Password Reset Flow
**Priority: HIGH - Missing Core Feature**

#### Step 2.1: Create PasswordResetToken Model
**File**: `app/models.py`
```python
class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(index=True, unique=True)  # SHA256 of actual token
    expires_at: datetime
    used_at: Optional[datetime] = None
```
**Motivation**: Database-backed tokens allow one-time use enforcement and immediate revocation. Storing hashes instead of raw tokens prevents database compromise from exposing reset links.

#### Step 2.2: Add Token Hashing Utilities
**File**: `app/security.py`
```python
import hashlib

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()
```
**Motivation**: Hashing tokens before storage prevents database dumps from revealing valid reset links.

#### Step 2.3: Implement Forgot Password Endpoint
**File**: `app/routers/ui.py`
```python
@router.post("/auth/forgot")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    csrf: str = Form(...),
    session: Session = Depends(get_session)
):
    verify_csrf(request, csrf)
    # Always return 202 to prevent email enumeration
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=sha256_hex(raw_token),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        session.add(reset_token)
        session.commit()
        # Queue email with link containing raw_token
        send_reset_email(email, raw_token)
    return Response(status_code=202)
```
**Motivation**:
- Always returning 202 prevents attackers from discovering valid emails
- One-hour expiry balances security with user convenience
- Token in URL, hash in database prevents database compromise exposure

#### Step 2.4: Implement Reset Password Form & Handler
**File**: `app/routers/ui.py`
```python
@router.get("/reset")
async def reset_page(request: Request, token: str):
    # Show password reset form

@router.post("/auth/reset")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    csrf: str = Form(...),
    session: Session = Depends(get_session)
):
    verify_csrf(request, csrf)
    token_hash = sha256_hex(token)
    reset_token = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
        .where(PasswordResetToken.expires_at > datetime.utcnow())
    ).first()

    if not reset_token:
        raise HTTPException(400, "Invalid or expired token")

    user = session.get(User, reset_token.user_id)
    user.hashed_password = get_password_hash(new_password)
    reset_token.used_at = datetime.utcnow()
    session.commit()
```
**Motivation**: One-time use (checking used_at) prevents token reuse. Expiry check ensures old tokens can't be used.

### Phase 3: HTMX-Optimized Response Handling
**Priority: MEDIUM - Better UX**

#### Step 3.1: Implement HX-Redirect Helper
**File**: `app/routers/ui.py`
```python
def hx_redirect(url: str, request: Request) -> Response:
    if request.headers.get("HX-Request"):
        response = Response(status_code=204)
        response.headers["HX-Redirect"] = url
        return response
    else:
        return RedirectResponse(url=url, status_code=303)
```
**Motivation**: HX-Redirect header tells HTMX to perform a full page navigation, cleaner than JavaScript window.location. Status 204 prevents content flash.

#### Step 3.2: Replace JavaScript Redirects
**Files**: All auth templates
- Remove `window.location.href = ...`
- Use HX-Redirect responses instead
**Motivation**: Native HTMX navigation is more reliable and doesn't require JavaScript execution.

#### Step 3.3: Implement Proper HTMX Error Handling
**File**: `app/templates/fragments/auth_error.html`
```html
<div id="auth-message" class="error" hx-swap-oob="true">
    {{ error }}
</div>
```
**Motivation**: Out-of-band swaps allow updating multiple page regions from a single response.

### Phase 4: Environment-Based Security Configuration
**Priority: MEDIUM - Production Readiness**

#### Step 4.1: Add Environment Detection
**File**: `app/config.py`
```python
class Settings(BaseSettings):
    environment: str = "development"  # or "production"

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"
```
**Motivation**: Secure flag should only be True on HTTPS (production), otherwise cookies won't work in development.

#### Step 4.2: Update All Cookie Settings
**Files**: All files setting cookies
```python
response.set_cookie(
    secure=settings.cookie_secure,  # Dynamic based on environment
    samesite="lax" if not settings.cookie_secure else "strict"
)
```
**Motivation**: Stricter settings in production while maintaining development usability.

### Phase 5: Enhanced Security Features
**Priority: LOW - Nice to Have**

#### Step 5.1: Add Password Changed Tracking
**File**: `app/models.py`
```python
class User(SQLModel, table=True):
    # ... existing fields ...
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
```
**Motivation**: Allows invalidating all tokens issued before password change, implementing "logout everywhere" after reset.

#### Step 5.2: Add Token Issued-At Validation
**File**: `app/auth.py`
```python
def validate_token_age(user: User, token_iat: datetime) -> bool:
    return token_iat > user.password_changed_at
```
**Motivation**: Ensures old tokens become invalid after password change without waiting for expiry.

#### Step 5.3: Implement Rate Limiting
**File**: `app/routers/auth.py`
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
```
**Motivation**: Prevents brute force attacks on login and password reset endpoints.

### Phase 6: Optional - FastAPI-Login Migration
**Priority: OPTIONAL - Code Simplification**

#### Why Consider This:
- **Pros**:
  - Battle-tested library
  - Simplified cookie management
  - Built-in remember-me functionality
  - Less custom code to maintain
- **Cons**:
  - Additional dependency
  - Current implementation already works
  - Learning curve for team

#### Migration Steps (if chosen):
1. Install fastapi-login
2. Replace custom JWT functions with LoginManager
3. Update user loader callbacks
4. Migrate existing tokens (one-time script)

## Implementation Order & Timeline

### Week 1: Critical Security
1. Implement CSRF protection (Phase 1) - 2 days
2. Test CSRF on all forms - 1 day
3. Deploy to staging - 1 day

### Week 2: Core Features
1. Implement password reset (Phase 2) - 3 days
2. Email integration setup - 1 day
3. Testing and edge cases - 1 day

### Week 3: UX & Production
1. HTMX optimization (Phase 3) - 2 days
2. Environment configuration (Phase 4) - 1 day
3. Production deployment prep - 2 days

### Week 4: Enhancement (Optional)
1. Enhanced security features (Phase 5) - 3 days
2. Performance testing - 1 day
3. Documentation update - 1 day

## Testing Strategy

### Security Testing
- [ ] CSRF token validation on all forms
- [ ] Password reset token expiry
- [ ] Token one-time use enforcement
- [ ] Email enumeration prevention

### Integration Testing
- [ ] Full authentication flow with HTMX
- [ ] Password reset end-to-end
- [ ] Cookie behavior across browsers
- [ ] Session persistence

### Performance Testing
- [ ] Rate limiting effectiveness
- [ ] Database query optimization
- [ ] Token validation speed

## Rollback Plan

Each phase is independently deployable. If issues arise:
1. Revert code changes
2. Keep database migrations (additive only)
3. Clear browser cookies if needed
4. Restore previous cookie settings

## Success Metrics

- Zero CSRF vulnerabilities in security scan
- Password reset completion rate > 90%
- No increase in authentication latency
- Reduced authentication-related support tickets

## Notes for Developers

1. **Why JWT in cookies over localStorage**:
   - HTMX automatically sends cookies, not headers
   - HttpOnly prevents XSS attacks
   - Works with browser navigation

2. **Why database tokens for reset**:
   - Can be immediately revoked
   - One-time use enforcement
   - Audit trail capability

3. **Why CSRF with HTMX**:
   - Forms are still vulnerable without it
   - SameSite=lax isn't enough for state-changing operations
   - Defense in depth principle

4. **Why keep SQLModel**:
   - Already working well
   - Type safety benefits
   - No migration benefit to raw SQLAlchemy

## Configuration Checklist

Before production deployment:
- [ ] Generate new SECRET_KEY (min 32 chars)
- [ ] Set environment="production"
- [ ] Configure email service
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure rate limiting thresholds
- [ ] Database backup strategy
- [ ] Log aggregation setup