#!/usr/bin/env python3
"""
Project setup script - automated setup for new deployments.

This script:
1. Generates a secure SECRET_KEY
2. Creates .env file from template
3. Initializes the database
4. Optionally creates a first admin user

Usage:
    python scripts/setup.py
    python scripts/setup.py --no-interactive
"""

import sys
import os
import secrets
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_secret_key() -> str:
    """Generate a secure random secret key."""
    return secrets.token_urlsafe(32)


def create_env_file(force: bool = False) -> bool:
    """
    Create .env file from .env.example if it doesn't exist.
    
    Args:
        force: If True, overwrite existing .env file
        
    Returns:
        True if file was created, False otherwise
    """
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists() and not force:
        print(f"  .env file already exists at {env_file}")
        return False
    
    if not env_example.exists():
        print(f"  Error: .env.example not found at {env_example}")
        return False
    
    # Read template
    with open(env_example, "r") as f:
        content = f.read()
    
    # Replace placeholder secret key with generated one
    secret_key = generate_secret_key()
    content = content.replace(
        "change-this-to-a-secure-random-string-at-least-32-chars",
        secret_key
    )
    
    # Write new .env file
    with open(env_file, "w") as f:
        f.write(content)
    
    print(f"  Created .env file with secure SECRET_KEY")
    return True


def init_database() -> bool:
    """
    Initialize the database by creating all tables.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from sqlmodel import SQLModel
        from app.database import engine
        from app import models  # noqa: F401 - Import to register models
        
        SQLModel.metadata.create_all(engine)
        print("  Database tables created successfully")
        return True
    except Exception as e:
        print(f"  Error initializing database: {e}")
        return False


def create_admin_user(email: str, password: str, full_name: str) -> bool:
    """
    Create an admin user.
    
    Args:
        email: Admin email
        password: Admin password
        full_name: Admin full name
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from sqlmodel import Session, select
        from app.database import engine
        from app.models import User
        from app.login_manager import get_password_hash
        
        with Session(engine) as session:
            # Check if user already exists
            existing = session.exec(
                select(User).where(User.email == email)
            ).first()
            
            if existing:
                print(f"  User with email {email} already exists")
                if not existing.is_superuser:
                    existing.is_superuser = True
                    session.add(existing)
                    session.commit()
                    print(f"  Promoted existing user to admin")
                return True
            
            # Create new admin user
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                is_superuser=True,
            )
            session.add(user)
            session.commit()
            
            print(f"  Created admin user: {email}")
            return True
            
    except Exception as e:
        print(f"  Error creating admin user: {e}")
        return False


def run_interactive_setup():
    """Run interactive setup wizard."""
    print("\n" + "=" * 50)
    print("FastAPI Starter Template - Setup Wizard")
    print("=" * 50 + "\n")
    
    # Step 1: Create .env file
    print("Step 1: Environment Configuration")
    print("-" * 35)
    
    env_file = project_root / ".env"
    if env_file.exists():
        response = input("  .env file exists. Overwrite? (yes/no) [no]: ").strip().lower()
        if response == "yes":
            create_env_file(force=True)
        else:
            print("  Keeping existing .env file")
    else:
        create_env_file()
    
    print()
    
    # Step 2: Initialize database
    print("Step 2: Database Initialization")
    print("-" * 35)
    init_database()
    print()
    
    # Step 3: Create admin user (optional)
    print("Step 3: Admin User (Optional)")
    print("-" * 35)
    response = input("  Create admin user? (yes/no) [yes]: ").strip().lower()
    
    if response != "no":
        email = input("  Admin email: ").strip()
        if not email:
            print("  Skipping admin user creation")
        else:
            full_name = input("  Admin full name [Admin]: ").strip() or "Admin"
            password = input("  Admin password: ").strip()
            
            if password:
                create_admin_user(email, password, full_name)
            else:
                print("  Skipping admin user creation (no password provided)")
    
    print()
    print("=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("  1. Review and update .env with your settings")
    print("  2. Run: uvicorn app.main:app --reload")
    print("  3. Visit: http://localhost:8000")
    print()


def run_non_interactive_setup():
    """Run non-interactive setup (for CI/CD)."""
    print("Running non-interactive setup...")
    
    # Create .env if it doesn't exist
    create_env_file()
    
    # Initialize database
    init_database()
    
    print("Setup complete!")


def main():
    """Main entry point."""
    if "--no-interactive" in sys.argv or "-n" in sys.argv:
        run_non_interactive_setup()
    elif "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
    else:
        run_interactive_setup()


if __name__ == "__main__":
    main()

