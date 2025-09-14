---
name: security-review
description: Comprehensive security analysis of authentication, authorization, and data access
arguments:
  - name: component
    description: Specific component to review (optional - defaults to full application)
    required: false
  - name: depth
    description: Review depth - quick, standard, or thorough (default: standard)
    required: false
---

# Security Review Command

## Purpose
Perform comprehensive security analysis covering authentication, authorization, data access controls, and common vulnerabilities. Goes beyond login flows to examine all aspects of user data protection and access control.

## Review Scope

### 1. Authentication & Session Management
- **Login/Logout Security**:
  - Timing attack vulnerabilities
  - Username enumeration
  - Brute force protection
  - Session fixation
  - Secure cookie configuration

- **Password Management**:
  - Password hashing (bcrypt with proper rounds)
  - Password complexity requirements
  - Password reset token security
  - Password change flow
  - Password history and reuse

- **Token Security**:
  - JWT signature verification
  - Token expiration handling
  - Token rotation on privilege changes
  - Remember me functionality

### 2. Authorization & Access Control
- **User Data Isolation**:
  ```python
  # Check patterns like:
  GET /users/{user_id}/profile  # Can user A access user B's profile?
  GET /api/documents/{doc_id}   # Can users access others' documents?
  PUT /users/{user_id}/settings # Can users modify others' settings?
  ```

- **Privilege Escalation**:
  - Horizontal: User accessing another user's data
  - Vertical: Regular user accessing admin functions
  - Direct object reference vulnerabilities
  - Missing function level access control

- **Admin Protection**:
  - Admin endpoints properly protected
  - Superuser flag checks
  - Admin action logging

### 3. Data Protection & Privacy
- **Sensitive Data Handling**:
  - PII protection in database
  - Data masking in logs
  - Sensitive data in error messages
  - Data exposure in API responses
  - Unnecessary data in tokens

- **Database Security**:
  - SQL injection vulnerabilities
  - Parameterized queries usage
  - Database permissions (file and user)
  - Connection string security

- **Information Disclosure**:
  - Debug information leakage
  - Stack traces in production
  - Version information exposure
  - Directory listing
  - Source code disclosure

### 4. Input/Output Security
- **Input Validation**:
  - All user inputs validated
  - Type checking and sanitization
  - File upload restrictions
  - Path traversal prevention
  - Command injection prevention

- **Output Encoding**:
  - XSS prevention in templates
  - JSON response sanitization
  - HTML encoding in user content
  - CORS configuration

### 5. Security Controls
- **CSRF Protection**:
  - All forms have CSRF tokens
  - Token validation on POST/PUT/DELETE
  - Double-submit cookie pattern
  - Token lifetime appropriate

- **Rate Limiting**:
  - Authentication endpoints
  - Password reset
  - API endpoints
  - Effectiveness against automation

- **Security Headers**:
  - Content-Security-Policy
  - X-Frame-Options
  - X-Content-Type-Options
  - Strict-Transport-Security
  - X-XSS-Protection

### 6. Logging & Monitoring
- **Security Event Logging**:
  - Failed login attempts
  - Authorization failures
  - Rate limit violations
  - Password changes
  - Admin actions

- **Log Security**:
  - No passwords in logs
  - No tokens in logs
  - PII masking
  - Log injection prevention

## Workflow

### Step 1: Automated Scanning
```bash
# Check for common issues
- Hardcoded secrets in code
- Debug mode in production
- Default credentials
- Outdated dependencies
- Known vulnerabilities (via pip audit)
```

### Step 2: Authentication Testing
1. Test login with timing analysis
2. Check for username enumeration
3. Verify rate limiting effectiveness
4. Test session management
5. Check password policies

### Step 3: Authorization Testing
1. Create multiple test users with different roles
2. Test cross-user data access:
   ```python
   # As User A, try to access:
   - User B's profile (/users/B/profile)
   - User B's settings (/users/B/settings)
   - User B's resources (/api/users/B/documents)
   ```
3. Test admin endpoint access as regular user
4. Check for IDOR vulnerabilities
5. Verify object-level authorization

### Step 4: Data Protection Analysis
1. Review database queries for injection risks
2. Check log files for sensitive data
3. Test error messages for information leakage
4. Review API responses for over-exposure
5. Check file permissions

### Step 5: Security Controls Verification
1. Test CSRF protection on all forms
2. Verify rate limiting thresholds
3. Check security headers presence
4. Test HTTPS enforcement
5. Review cookie security flags

## Output Format

```markdown
# Security Review Report

## Executive Summary
- Overall Score: X/10
- Critical Issues: X
- High Issues: X
- Medium Issues: X
- Low Issues: X

## Critical Findings

### 1. [Vulnerability Name]
**Severity**: Critical
**Component**: [Affected component]
**Description**: [What the issue is]
**Impact**: [What could happen]
**Proof of Concept**:
```python
# Code to demonstrate issue
```
**Recommendation**: [How to fix]
**Fix Priority**: Immediate

## Authorization Test Results

### User Data Isolation
- ✅/❌ Users can only access their own profiles
- ✅/❌ Users can only modify their own settings
- ✅/❌ API endpoints enforce ownership checks
- ✅/❌ No direct object reference vulnerabilities

### Admin Protection
- ✅/❌ Admin endpoints require superuser flag
- ✅/❌ Regular users cannot access admin functions
- ✅/❌ Admin actions are logged

## Compliance Checklist

### OWASP Top 10 Coverage
- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Authentication Failures
- [ ] A08: Data Integrity Failures
- [ ] A09: Logging Failures
- [ ] A10: SSRF

## Recommendations
1. Priority 1 (Critical - Fix Immediately)
2. Priority 2 (High - Fix This Week)
3. Priority 3 (Medium - Fix This Month)
4. Priority 4 (Low - Fix This Quarter)
```

## Testing Commands
```bash
# Test user isolation
curl -X GET https://domain/users/1/profile -H "Cookie: access-token=user2_token"

# Test rate limiting
for i in {1..20}; do curl -X POST https://domain/auth/login -d "..." ; done

# Check security headers
curl -I https://domain | grep -E "X-Frame-Options|Content-Security-Policy"

# Test CSRF protection
curl -X POST https://domain/users/me -H "Cookie: access-token=..." -d "name=test"
```

## Examples
```
/security-review                    # Full application review
/security-review authentication     # Auth system only
/security-review "user endpoints"   # User data access review
/security-review api thorough       # Detailed API security review
```

## Severity Ratings
- **Critical**: Immediate exploitation possible, high impact
- **High**: Exploitation likely, significant impact
- **Medium**: Exploitation possible, moderate impact
- **Low**: Exploitation unlikely, minimal impact
- **Info**: Best practice recommendation