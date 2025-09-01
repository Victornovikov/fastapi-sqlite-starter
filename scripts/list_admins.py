#!/usr/bin/env python3
"""
Script to list all admin users in the system.
Run this script on the server with direct database access.

Usage:
    python scripts/list_admins.py
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.database import engine
from app.models import User


def list_admin_users():
    """List all users with admin (superuser) status."""
    with Session(engine) as session:
        # Find all admin users
        statement = select(User).where(User.is_superuser == True)
        admins = session.exec(statement).all()
        
        if not admins:
            print("ℹ️  No admin users found in the system.")
            print("   Use 'python scripts/promote_to_admin.py <username>' to create one.")
            return
        
        print(f"👑 Admin Users ({len(admins)} total):")
        print("-" * 60)
        
        for admin in admins:
            print(f"\n📌 {admin.username}")
            print(f"   - ID: {admin.id}")
            print(f"   - Email: {admin.email}")
            print(f"   - Full Name: {admin.full_name or 'Not set'}")
            print(f"   - Active: {'✅' if admin.is_active else '❌'}")
            print(f"   - Created: {admin.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main function."""
    # Check if database exists
    db_path = Path("app.db")
    if not db_path.exists():
        print(f"❌ Error: Database file '{db_path}' not found.")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    list_admin_users()


if __name__ == "__main__":
    main()
