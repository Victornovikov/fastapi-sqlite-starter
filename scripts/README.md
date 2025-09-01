# Admin Management Scripts

This directory contains scripts for managing admin users in the FastAPI application.

## Security Note

These scripts require direct server access and database permissions. They are designed to be run manually by system administrators and should **never** be exposed through the web API.

## Available Scripts

### promote_to_admin.py

Promotes a regular user to admin (superuser) status.

**Usage:**
```bash
python scripts/promote_to_admin.py <username>
```

**Example:**
```bash
# First, the user registers normally through the API
# Then, promote them to admin:
python scripts/promote_to_admin.py johndoe
```

**Features:**
- Validates that the user exists
- Requires confirmation before making changes
- Shows user details after promotion
- Prevents double-promotion (safe to run multiple times)

### list_admins.py

Lists all users with admin privileges.

**Usage:**
```bash
python scripts/list_admins.py
```

**Output includes:**
- Username
- User ID
- Email address
- Full name
- Active status
- Account creation date

## Setup Instructions

1. Ensure you're in the project root directory
2. The database file (`app.db`) must exist
3. Python environment with project dependencies must be activated

## Security Best Practices

1. **Run only on the server**: These scripts should only be executed on the production server with proper access controls
2. **Audit trail**: Keep logs of who was promoted to admin and when
3. **Principle of least privilege**: Only promote users who absolutely need admin access
4. **Regular reviews**: Periodically review admin users and revoke unnecessary privileges

## Workflow Example

```bash
# 1. User registers through the API
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "SecurePass123!", "full_name": "System Admin"}'

# 2. SSH into the server and navigate to project directory
cd /path/to/fastapi-app

# 3. Check current admins
python scripts/list_admins.py

# 4. Promote the user
python scripts/promote_to_admin.py admin

# 5. Verify the promotion
python scripts/list_admins.py
```

## Troubleshooting

**"Database file not found" error:**
- Make sure you're running the script from the project root directory
- Check that the application has been run at least once to create the database

**"User not found" error:**
- Verify the username is correct (case-sensitive)
- Ensure the user has registered through the `/auth/register` endpoint first

**Import errors:**
- Activate the Python virtual environment
- Install all requirements: `pip install -r requirements.txt`
