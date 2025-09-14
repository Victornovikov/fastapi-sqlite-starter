---
name: commit
description: Create a git commit with security checks and project standards
arguments:
  - name: message
    description: Optional commit message (will be generated if not provided)
    required: false
  - name: type
    description: Commit type - feat, fix, security, docs, test, refactor (default: auto-detect)
    required: false
---

# Commit Command

## Purpose
Create standardized git commits with security checks, proper formatting, and Claude co-authorship attribution. Ensures no sensitive data is committed and follows project conventions.

## Pre-Commit Security Checks

### 1. Sensitive Data Detection
- **API Keys & Secrets**:
  ```regex
  (api[_-]?key|apikey|secret|password|pwd|token|auth)[\s]*=[\s]*["'][^"']+["']
  ```
- **Private Keys**: Check for BEGIN RSA/DSA/EC PRIVATE KEY
- **AWS Credentials**: AWS access key patterns
- **Database URLs**: Connection strings with passwords
- **JWT Secrets**: Hardcoded JWT signing keys

### 2. Code Quality Checks
- **Debug Code**:
  - `console.log()` statements
  - `print()` debugging statements
  - `debugger;` statements
  - `import pdb; pdb.set_trace()`

- **Commented Security**:
  - Commented out authentication checks
  - Disabled CSRF protection
  - Bypassed rate limiting

### 3. File Permissions
- Database files have correct permissions (664)
- Log files are properly configured
- No executable files added accidentally

## Workflow

### Step 1: Analyze Changes
```bash
# Run in parallel for efficiency
- git status
- git diff --staged
- git diff
- git log --oneline -5
```

### Step 2: Security Scan
1. Check for sensitive data in changes
2. Verify no debug code remains
3. Ensure no security controls disabled
4. Check file permissions if database files changed
5. Verify no .env or secrets files being committed

### Step 3: Run Tests (if applicable)
```bash
# Run tests for changed components
- If auth files changed: pytest tests/test_auth.py
- If user files changed: pytest tests/test_user*.py
- If new feature: pytest tests/test_[feature].py
```

### Step 4: Generate Commit Message

#### Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types:
- **feat**: New feature
- **fix**: Bug fix
- **security**: Security improvement
- **docs**: Documentation only
- **test**: Tests only
- **refactor**: Code restructuring
- **perf**: Performance improvement
- **style**: Code style changes
- **chore**: Maintenance tasks

#### Example Messages:
```
feat(auth): add change password functionality

- Implement password change endpoint with current password verification
- Add CSRF protection and rate limiting (5/min)
- Prevent reusing same password
- Include comprehensive security logging
- Add tests for all edge cases

Security: Rate limited, CSRF protected, requires authentication
Tests: All passing (7 new tests added)

🤖 Generated with Claude Code
Co-authored-by: Claude <noreply@anthropic.com>
```

### Step 5: Stage Files
```bash
# Intelligent staging
- Stage modified application files
- Stage new test files
- Stage updated documentation
- Exclude: .pyc, __pycache__, logs, .env
- Warn about: large files, binary files
```

### Step 6: Create Commit
```bash
git commit -m "$(cat <<'EOF'
[generated message]

🤖 Generated with Claude Code
Co-authored-by: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 7: Post-Commit Verification
- Verify commit created successfully
- Show commit hash and summary
- Suggest next steps (push, PR, deploy)

## Security Checklist
- [ ] No hardcoded secrets or API keys
- [ ] No debug code or print statements
- [ ] No commented-out security controls
- [ ] No sensitive data in commit message
- [ ] No .env or credential files
- [ ] Database files have correct permissions
- [ ] Tests pass for changed components
- [ ] No large binary files accidentally included

## Output Format
```
🔍 Security Check: ✅ Passed
📝 Changes Summary:
  - Modified: 3 files
  - Added: 2 files
  - Deleted: 0 files

🧪 Tests: ✅ All passing (15 tests)

📦 Commit Created:
  Hash: abc1234
  Type: feat(auth)
  Message: Add change password functionality

✨ Next Steps:
  - Push to remote: git push origin feature/change-password
  - Create PR: gh pr create
  - Deploy: sudo systemctl restart fastapi-app
```

## Error Handling

### Common Issues:
1. **Sensitive data detected**:
   - Show location of sensitive data
   - Refuse to commit
   - Suggest using environment variables

2. **Tests failing**:
   - Show which tests failed
   - Offer to commit anyway with [skip-tests] tag
   - Suggest fixing tests first

3. **No changes staged**:
   - Show available changes
   - Offer to stage all changes
   - Or stage selected files

4. **Database permission issues**:
   - Auto-fix permissions if possible
   - Show correct permission commands
   - Warn about SystemD service impact

## Examples
```
/commit                                    # Auto-generate message
/commit "Add user profile editing"        # Custom message
/commit "Fix login bug" fix              # Specify type
/commit --no-tests                       # Skip test running
/commit --security-only                  # Only security checks
```

## Configuration
Reads from project standards:
- Commit message format from previous commits
- Test commands from package.json or Makefile
- Security patterns from .gitleaks.toml (if exists)
- Ignore patterns from .gitignore

## Best Practices
1. Commit frequently with focused changes
2. Write clear, descriptive messages
3. Always run security checks
4. Include tests with features
5. Reference issue numbers when applicable
6. Keep commits atomic and reversible