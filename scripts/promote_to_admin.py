#!/usr/bin/env python3
"""
Script to promote a regular user to admin (superuser) status.
Run this script on the server with direct database access.

Usage:
    python scripts/promote_to_admin.py <email>
    
Example:
    python scripts/promote_to_admin.py admin@example.com
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.database import engine
from app.models import User


def promote_user_to_admin(email: str) -> bool:
    """
    Promote a user to admin status by setting is_superuser to True.
    
    Args:
        email: The email of the user to promote
        
    Returns:
        True if successful, False otherwise
    """
    with Session(engine) as session:
        # Find the user by email
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if not user:
            print(f"❌ Error: User with email '{email}' not found.")
            return False
        
        if user.is_superuser:
            print(f"ℹ️  User '{email}' is already an admin.")
            return True
        
        # Promote to admin
        user.is_superuser = True
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"✅ Successfully promoted '{email}' to admin.")
        print(f"   User details:")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - Full Name: {user.full_name}")
        print(f"   - Active: {user.is_active}")
        print(f"   - Admin: {user.is_superuser}")
        
        return True


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_to_admin.py <email>")
        print("Example: python scripts/promote_to_admin.py admin@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Confirm the action
    print(f"⚠️  WARNING: This will grant admin privileges to user '{email}'.")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Operation cancelled.")
        sys.exit(0)
    
    # Check if database exists
    db_path = Path("app.db")
    if not db_path.exists():
        print(f"❌ Error: Database file '{db_path}' not found.")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Promote the user
    success = promote_user_to_admin(email)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
