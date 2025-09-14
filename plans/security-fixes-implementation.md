# Security Fixes Implementation Plan

## Overview
Address critical security vulnerabilities and enhance authentication system security based on the security review findings.

## Priority Levels
- **P1 (Critical)**: Fix immediately - timing attacks and data exposure
- **P2 (High)**: Fix this week - account protection and notifications
- **P3 (Medium)**: Fix this month - enhanced security features
- **P4 (Low)**: Fix this quarter - nice-to-have improvements

---

## Phase 1: Critical Security Fixes (P1) - Immediate

### 1.1 Fix Timing Attack Vulnerability in Login
- [ ] Modify `authenticate_user()` in `app/login_manager.py`
- [ ] Always perform bcrypt verification even for non-existent users
- [ ] Use dummy hash for consistent timing: `$2b$12$dummy.hash.to.prevent.timing.attacks`
- [ ] Test timing consistency between valid/invalid users
- [ ] Verify fix doesn't break existing login functionality
- [ ] Update tests to check for timing attack prevention

**Code location**: `app/login_manager.py:83-99`

### 1.2 Remove Sensitive Data from Debug Logs
- [ ] Audit all logger.debug() calls in authentication code
- [ ] Replace email addresses with masked versions in debug logs
- [ ] Create `mask_email()` utility function
- [ ] Update logging in `app/login_manager.py`
- [ ] Update logging in `app/routers/ui.py`
- [ ] Review `app/routers/auth.py` for similar issues

**Affected files**:
- `app/login_manager.py`: lines 60, 68, 76, 91, 94
- `app/routers/ui.py`: check all auth endpoints
- `app/routers/auth.py`: check all endpoints

---

## Phase 2: High Priority Fixes (P2) - This Week

### 2.1 Prevent Username Enumeration
- [ ] Modify registration endpoint to use generic messages
- [ ] Update `POST /auth/register` in `app/routers/ui.py`
- [ ] Update `POST /auth/signup` in `app/routers/ui.py`
- [ ] Consider sending verification email instead of immediate error
- [ ] Update error messages to be generic
- [ ] Test that timing is consistent for existing/non-existing emails

**Generic message**: "If this email is not already registered, you will receive a confirmation email"

### 2.2 Implement Account Lockout
- [ ] Add `failed_login_attempts` field to User model
- [ ] Add `locked_until` timestamp field to User model
- [ ] Create database migration for new fields
- [ ] Implement lockout logic in `authenticate_user()`
- [ ] Add configuration for max attempts (default: 5)
- [ ] Add configuration for lockout duration (default: 15 minutes)
- [ ] Create unlock mechanism (time-based or admin action)
- [ ] Add logging for lockout events
- [ ] Create tests for lockout functionality

**Configuration**:
```python
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
```

### 2.3 Add Security Event Email Notifications
- [ ] Create email templates for security events
- [ ] Implement password change notification
- [ ] Implement suspicious login notification
- [ ] Implement account lockout notification
- [ ] Add email sending to password change flow
- [ ] Add email sending to login from new location
- [ ] Make notifications configurable (on/off)
- [ ] Test email delivery

**Events to notify**:
- Password changed successfully
- Login from new IP/location
- Account locked due to failed attempts
- Password reset requested

---

## Phase 3: Medium Priority Enhancements (P3) - This Month

### 3.1 Add Password Complexity Requirements
- [ ] Create password validation function
- [ ] Add configurable complexity rules
- [ ] Implement minimum length check (current: 8)
- [ ] Add uppercase letter requirement (optional)
- [ ] Add lowercase letter requirement (optional)
- [ ] Add number requirement (optional)
- [ ] Add special character requirement (optional)
- [ ] Update password change endpoint
- [ ] Update registration endpoint
- [ ] Update password reset endpoint
- [ ] Add client-side validation hints
- [ ] Create tests for password validation

**Default configuration**:
```python
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = False
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = False
```

### 3.2 Implement Session Token Rotation
- [ ] Add token rotation on login
- [ ] Add token rotation on password change
- [ ] Add token rotation on privilege escalation
- [ ] Implement old token grace period (5 seconds)
- [ ] Update session management logic
- [ ] Test token rotation doesn't break active sessions
- [ ] Add logging for token rotation events

### 3.3 Fix CSRF Token Lifetime
- [ ] Tie CSRF token lifetime to session duration
- [ ] Regenerate CSRF on login
- [ ] Clear CSRF on logout
- [ ] Update `generate_csrf_token()` to accept expiry
- [ ] Update all endpoints using CSRF
- [ ] Test CSRF expiry behavior

### 3.4 Implement Password History
- [ ] Create PasswordHistory model
- [ ] Store last 5 password hashes
- [ ] Check new password against history
- [ ] Implement configurable history depth
- [ ] Add database migration
- [ ] Update password change logic
- [ ] Create tests for password history

---

## Phase 4: Low Priority Improvements (P4) - This Quarter

### 4.1 Add Two-Factor Authentication (2FA)
- [ ] Research 2FA libraries (pyotp recommended)
- [ ] Add `totp_secret` field to User model
- [ ] Create 2FA setup endpoint
- [ ] Generate QR codes for authenticator apps
- [ ] Implement TOTP verification
- [ ] Add backup codes generation
- [ ] Create 2FA verification page
- [ ] Update login flow for 2FA users
- [ ] Add 2FA disable option
- [ ] Create comprehensive tests

### 4.2 Implement CAPTCHA for Failed Logins
- [ ] Integrate reCAPTCHA or hCaptcha
- [ ] Add CAPTCHA after 3 failed attempts
- [ ] Create CAPTCHA verification endpoint
- [ ] Update login form to show CAPTCHA
- [ ] Add CAPTCHA configuration
- [ ] Test CAPTCHA flow
- [ ] Ensure accessibility compliance

### 4.3 Add "Logout All Sessions" Feature
- [ ] Implement session tracking
- [ ] Store active sessions in database
- [ ] Create logout all endpoint
- [ ] Add UI button in profile
- [ ] Invalidate all tokens except current
- [ ] Send notification email
- [ ] Test multi-device scenarios

### 4.4 Implement Security Headers
- [ ] Add Content-Security-Policy header
- [ ] Add X-Frame-Options header
- [ ] Add X-Content-Type-Options header
- [ ] Add Strict-Transport-Security header
- [ ] Add X-XSS-Protection header
- [ ] Create middleware for security headers
- [ ] Test headers don't break functionality
- [ ] Document CSP requirements

### 4.5 Add Anomaly Detection
- [ ] Track login patterns per user
- [ ] Detect unusual login times
- [ ] Detect unusual login locations
- [ ] Implement risk scoring
- [ ] Add additional verification for risky logins
- [ ] Create admin dashboard for security events
- [ ] Test detection accuracy

---

## Implementation Guidelines

### Testing Requirements
- [ ] Write unit tests for each security fix
- [ ] Perform penetration testing after P1 fixes
- [ ] Test rate limiting effectiveness
- [ ] Verify no performance degradation
- [ ] Test across different browsers
- [ ] Test with multiple concurrent users

### Documentation Updates
- [ ] Update CLAUDE.md with new security features
- [ ] Update API documentation
- [ ] Create security best practices guide
- [ ] Document configuration options
- [ ] Update deployment guide

### Monitoring & Alerts
- [ ] Set up alerts for multiple failed logins
- [ ] Monitor for timing attack attempts
- [ ] Track account lockout frequency
- [ ] Monitor rate limit violations
- [ ] Create security dashboard

### Rollback Plan
- [ ] Create database backups before migrations
- [ ] Tag git repository before each phase
- [ ] Document rollback procedures
- [ ] Test rollback process in staging
- [ ] Keep previous version deployed as backup

---

## Success Metrics

### Phase 1 Success Criteria
- [ ] Zero timing difference between valid/invalid users (< 50ms variance)
- [ ] No sensitive data in log files
- [ ] All tests passing

### Phase 2 Success Criteria
- [ ] Account lockout working correctly
- [ ] Email notifications sending
- [ ] No username enumeration possible

### Phase 3 Success Criteria
- [ ] Password complexity enforced
- [ ] Session tokens rotating properly
- [ ] Password history preventing reuse

### Phase 4 Success Criteria
- [ ] 2FA functional for enabled users
- [ ] Security headers present on all responses
- [ ] Anomaly detection catching suspicious activity

---

## Timeline

| Phase | Priority | Target Date | Estimated Hours |
|-------|----------|-------------|-----------------|
| Phase 1 | Critical | Immediate (Today) | 4 hours |
| Phase 2 | High | Within 7 days | 16 hours |
| Phase 3 | Medium | Within 30 days | 24 hours |
| Phase 4 | Low | Within 90 days | 40 hours |

## Risk Assessment

### Risks During Implementation
1. **Breaking existing authentication** - Mitigate with comprehensive testing
2. **Performance impact** - Monitor response times after timing attack fix
3. **User experience degradation** - Balance security with usability
4. **Email delivery issues** - Implement retry logic and fallbacks
5. **Database migration failures** - Test migrations thoroughly in staging

### Post-Implementation Risks
1. **Increased support requests** - Prepare documentation and FAQs
2. **User lockouts** - Implement admin unlock capability
3. **False positive in anomaly detection** - Start with logging only, then enforce

---

## Notes

- Always test security fixes in development first
- Consider hiring security consultant for Phase 4 (2FA implementation)
- Maintain backward compatibility where possible
- Keep security fixes separate from feature development
- Document all security decisions and trade-offs

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)