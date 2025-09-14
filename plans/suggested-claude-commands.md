# Suggested Claude Commands for FastAPI-SQLite Project

Based on our conversation patterns, these custom commands would streamline common tasks:

## Security & Testing Commands

### /security-review
**Purpose**: Conduct a thorough security review of authentication flows
**What it does**:
- Reviews login, registration, and password change flows
- Checks for timing attacks, CSRF, rate limiting
- Examines session management and password storage
- Creates a security report with findings and recommendations
**Usage**: `/security-review [component]`

### /test-feature
**Purpose**: Test a newly implemented feature
**What it does**:
- Writes comprehensive tests for the feature
- Runs tests and checks for failures
- Validates against security best practices
- Checks database permissions
**Usage**: `/test-feature [feature-name]`

## Development Workflow Commands

### /implement-feature
**Purpose**: Implement a new feature following best practices
**What it does**:
1. Creates a detailed plan in `/plans/`
2. Creates a new git branch
3. Uses TodoWrite to track progress
4. Follows patterns from `templates_snippets.md`
5. Implements with proper CSRF, rate limiting, logging
6. Writes tests
7. Updates documentation
**Usage**: `/implement-feature "Add user profile editing"`

### /fix-permissions
**Purpose**: Fix file and database permissions for SystemD service
**What it does**:
- Checks and fixes database file permissions (664)
- Sets correct ownership (appuser:appuser)
- Fixes log file permissions
- Restarts SystemD service
**Usage**: `/fix-permissions`

### /check-deployment
**Purpose**: Verify production deployment status
**What it does**:
- Checks SystemD service status
- Verifies database permissions
- Reviews recent logs for errors
- Tests key endpoints
- Checks Cloudflare tunnel status
**Usage**: `/check-deployment`

## Git & Documentation Commands

### /prepare-commit
**Purpose**: Prepare and create a git commit following project standards
**What it does**:
1. Runs `git status` and `git diff`
2. Reviews changes for security issues
3. Stages relevant files
4. Creates commit with proper message format
5. Includes co-author attribution for Claude
**Usage**: `/prepare-commit`

### /update-docs
**Purpose**: Update project documentation
**What it does**:
- Updates CLAUDE.md with new patterns
- Updates templates_snippets.md with code examples
- Creates/updates plans in `/plans/`
- Updates security documentation
**Usage**: `/update-docs [component]`

## Debugging Commands

### /debug-error
**Purpose**: Debug an error with full context
**What it does**:
- Checks application logs
- Reviews SystemD journal
- Examines error patterns
- Checks database permissions
- Reviews recent code changes
- Suggests fixes
**Usage**: `/debug-error "500 error on password change"`

### /check-logs
**Purpose**: Review application logs for issues
**What it does**:
- Tails application logs
- Greps for errors and warnings
- Checks for security events
- Reviews rate limiting violations
- Summarizes findings
**Usage**: `/check-logs [timeframe]`

## Database Commands

### /db-status
**Purpose**: Check database status and integrity
**What it does**:
- Verifies database file exists and permissions
- Checks WAL mode status
- Reviews table structure
- Validates foreign keys
- Checks for locks
**Usage**: `/db-status`

## Testing Shortcuts

### /test-auth
**Purpose**: Run all authentication-related tests
**What it does**:
- Runs login, registration, password reset tests
- Tests rate limiting
- Validates CSRF protection
- Checks for timing attacks
**Usage**: `/test-auth`

### /test-security
**Purpose**: Run security-focused tests
**What it does**:
- Tests for SQL injection
- Checks for XSS vulnerabilities
- Validates CSRF protection
- Tests rate limiting
- Checks password hashing
**Usage**: `/test-security`

## Deployment Commands

### /deploy-changes
**Purpose**: Deploy changes to production
**What it does**:
1. Runs tests locally
2. Commits changes
3. Pushes to repository
4. Restarts SystemD service
5. Verifies deployment
6. Checks logs for errors
**Usage**: `/deploy-changes "Feature description"`

### /rollback
**Purpose**: Rollback to previous version
**What it does**:
- Creates backup of current state
- Checks out previous commit
- Restarts services
- Verifies rollback success
**Usage**: `/rollback [commit-hash]`

## Project-Specific Commands

### /add-endpoint
**Purpose**: Add a new API endpoint with all requirements
**What it does**:
- Creates route with proper authentication
- Adds CSRF protection for UI routes
- Implements rate limiting
- Adds logging
- Creates tests
- Updates API documentation
**Usage**: `/add-endpoint POST /api/users/settings`

### /check-csrf
**Purpose**: Verify CSRF protection on all forms
**What it does**:
- Scans all HTML templates for forms
- Verifies CSRF token generation in routes
- Checks token validation in POST handlers
- Reports any missing protections
**Usage**: `/check-csrf`

## Maintenance Commands

### /cleanup
**Purpose**: Clean up temporary files and logs
**What it does**:
- Removes .pyc files
- Cleans __pycache__ directories
- Rotates logs if needed
- Removes test databases
- Cleans temporary test files
**Usage**: `/cleanup`

### /health-check
**Purpose**: Comprehensive system health check
**What it does**:
- Checks all services are running
- Verifies database connectivity
- Tests authentication flow
- Checks disk space
- Reviews error rates in logs
**Usage**: `/health-check`

---

## Implementation Priority

### High Priority (Most Useful)
1. `/implement-feature` - Ensures consistent feature development
2. `/security-review` - Critical for maintaining security
3. `/prepare-commit` - Standardizes git workflow
4. `/debug-error` - Speeds up troubleshooting
5. `/fix-permissions` - Common issue resolver

### Medium Priority
6. `/test-feature` - Improves test coverage
7. `/check-deployment` - Production monitoring
8. `/update-docs` - Keeps documentation current
9. `/check-logs` - Log analysis
10. `/add-endpoint` - API development

### Low Priority (Nice to Have)
11. `/db-status` - Database health
12. `/cleanup` - Maintenance
13. `/rollback` - Emergency recovery
14. `/health-check` - System monitoring

---

## Notes for Implementation

- Commands should follow the existing `/plan` pattern
- Should integrate with TodoWrite for tracking
- Should respect CLAUDE.md guidelines
- Should use templates from templates_snippets.md
- Should include error handling and validation
- Should provide clear output and next steps