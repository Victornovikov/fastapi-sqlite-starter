# Change Password Feature Implementation Plan

## Overview
Implement a change password functionality for the /profile page that follows the existing HTMX-based web application patterns with proper security measures.

## Implementation Steps

### 1. Frontend - Update Profile Template
- [ ] Update `app/templates/profile.html` to replace disabled "Change Password" button with functional button
- [ ] Add a modal/dialog section for the password change form
- [ ] Include CSRF token generation and handling in the form
- [ ] Add HTMX attributes for form submission (hx-post, hx-target, hx-swap)
- [ ] Add form fields: current password, new password, confirm new password
- [ ] Add client-side password match validation indicator
- [ ] Style the modal using existing Pico CSS classes

### 2. Frontend - Create Response Fragments
- [ ] Create `app/templates/fragments/password_change_success.html` for success message
- [ ] Implement HTMX swap response for successful password change
- [ ] Add auto-close functionality for modal on success
- [ ] Reuse existing `auth_error.html` pattern for error messages
- [ ] Add specific error messages for different failure scenarios

### 3. Backend - Add Password Change Route
- [ ] Add `POST /auth/change-password` endpoint in `app/routers/ui.py`
- [ ] Implement authentication check using `Depends(manager)` or `get_current_user_optional`
- [ ] Add CSRF token verification using `verify_csrf()` function
- [ ] Validate form inputs (current_password, new_password, confirm_password)
- [ ] Verify current password using `verify_password()` from `app.login_manager`
- [ ] Check that new password and confirmation match
- [ ] Hash new password using `get_password_hash()` from `app.login_manager`
- [ ] Update user's hashed_password in database
- [ ] Commit database changes
- [ ] Return appropriate HTMX response (success fragment or error)

### 4. Security Features
- [ ] Add rate limiting decorator `@auth_limiter.limit("5/minute")` to prevent brute force
- [ ] Implement CSRF protection following double-submit cookie pattern
- [ ] Add comprehensive logging for all password change attempts
- [ ] Log successful password changes with user email and IP
- [ ] Log failed attempts with reason (wrong current password, mismatch, etc.)
- [ ] Ensure error messages don't reveal whether current password was correct
- [ ] Add password strength validation (minimum length, complexity requirements)

### 5. User Experience Enhancements
- [ ] Keep user logged in after successful password change (no session invalidation)
- [ ] Show loading state during form submission
- [ ] Clear form fields after successful change
- [ ] Add visual feedback for password strength
- [ ] Implement focus management for accessibility
- [ ] Add keyboard shortcuts (ESC to close modal)

### 6. Testing Considerations
- [ ] Test with correct current password
- [ ] Test with incorrect current password
- [ ] Test with mismatched new passwords
- [ ] Test rate limiting (exceed 5 attempts per minute)
- [ ] Test CSRF protection (missing or invalid token)
- [ ] Test while logged out (should redirect to login)
- [ ] Test password hashing and verification
- [ ] Test database update and persistence
- [ ] Test logging output for security events

## Code Structure

### Route Handler Structure
```python
@router.post("/auth/change-password", response_class=HTMLResponse)
@auth_limiter.limit("5/minute")
async def handle_change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    csrf: str = Form(...),
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    # Implementation here
```

### Modal HTML Structure
```html
<dialog id="change-password-modal">
    <article>
        <header>
            <h3>Change Password</h3>
            <button aria-label="Close" rel="prev" onclick="this.closest('dialog').close()">×</button>
        </header>
        <form hx-post="/auth/change-password" hx-target="#password-message">
            <!-- Form fields here -->
        </form>
    </article>
</dialog>
```

## Success Criteria
- User can successfully change their password from the profile page
- All security measures are in place and working
- User experience is smooth with proper feedback
- Changes follow existing codebase patterns and conventions
- All edge cases are handled gracefully
- Security events are properly logged