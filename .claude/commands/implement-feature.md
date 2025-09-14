---
name: implement-feature
description: Implement a new feature following security best practices and project patterns
arguments:
  - name: feature_name
    description: Name of the feature to implement (e.g., "user profile editing", "email notifications")
    required: true
---

# Implement Feature Command

## Purpose
Automate the complete feature implementation workflow with security-first approach, ensuring consistency with project patterns and comprehensive testing.

## Workflow

### Phase 1: Planning
1. Create detailed implementation plan in `/plans/[feature-name]-implementation.md`
2. Include security considerations:
   - Authentication requirements
   - Authorization rules
   - Data validation needs
   - Rate limiting requirements
3. Break down into checklistable tasks
4. Identify affected components

### Phase 2: Setup
1. Create new git branch: `feature/[feature-name]`
2. Initialize TodoWrite tracking with all implementation steps
3. Review similar existing features for patterns

### Phase 3: Implementation
1. **Backend Implementation**:
   - Create/modify routes in `app/routers/`
   - Add authentication: `Depends(manager)` or `get_current_user_optional`
   - Add authorization checks (user can only access their own data)
   - Implement rate limiting where appropriate
   - Add comprehensive logging with `logger.info()` and `logger.warning()`
   - Add input validation using Pydantic models

2. **For UI Routes (HTML/HTMX)**:
   - Generate CSRF token in route handler
   - Pass CSRF token to template context
   - Set CSRF cookie in response
   - Include CSRF token in forms
   - Return HTML fragments for errors
   - Use templates from `app/templates/`

3. **For API Routes (JSON)**:
   - Implement proper status codes
   - Return JSON responses
   - Document with OpenAPI schemas
   - Support both cookie and header auth

4. **Database Changes** (if needed):
   - Update models in `app/models.py`
   - Update schemas in `app/schemas.py`
   - Ensure proper session handling
   - Use `session.get(Model, id)` for updates

### Phase 4: Security Implementation
1. **Access Control**:
   - Verify users can only access their own resources
   - Check admin-only endpoints are protected
   - Test for privilege escalation vulnerabilities

2. **Input Validation**:
   - Validate all user inputs
   - Sanitize data before storage
   - Check for SQL injection vulnerabilities

3. **Output Security**:
   - Mask sensitive data in logs
   - Ensure error messages don't leak information
   - Add proper response headers

### Phase 5: Testing
1. Write comprehensive tests in `tests/test_[feature].py`:
   - Happy path tests
   - Authentication tests
   - Authorization tests (user isolation)
   - Input validation tests
   - Rate limiting tests
   - CSRF protection tests
   - Error handling tests

2. Run tests and fix any failures:
   ```bash
   pytest tests/test_[feature].py -v
   ```

### Phase 6: Documentation
1. Update `CLAUDE.md` with new patterns or guidelines
2. Update `templates_snippets.md` with reusable code
3. Add API documentation if new endpoints created
4. Document configuration options

### Phase 7: Review
1. Run security checks on implementation
2. Verify no hardcoded secrets
3. Check database permissions
4. Test with SystemD service
5. Review logs for errors

## Templates
Reference patterns from:
- `/opt/fastapi-sqlite/templates_snippets.md` - Code templates
- `/opt/fastapi-sqlite/CLAUDE.md` - Project guidelines
- Similar features in `app/routers/` for consistency

## Security Checklist
- [ ] Authentication required where needed
- [ ] Authorization checks prevent cross-user access
- [ ] CSRF protection on all forms
- [ ] Rate limiting on sensitive operations
- [ ] Input validation and sanitization
- [ ] Sensitive data masked in logs
- [ ] Error messages don't leak information
- [ ] Database operations use parameterized queries
- [ ] Tests cover security scenarios

## Output
1. Implementation plan in `/plans/`
2. Feature branch with implementation
3. Comprehensive tests
4. Updated documentation
5. Security validation report

## Examples
```
/implement-feature "user profile editing"
/implement-feature "email notifications"
/implement-feature "api key management"
/implement-feature "file upload"
```

## Error Handling
- Check existing patterns before implementing
- Verify database permissions for SystemD service
- Ensure CSRF tokens are properly handled
- Test with both development and production settings