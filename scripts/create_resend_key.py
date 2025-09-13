#!/usr/bin/env python3
"""
One-time script to create a sending_access scoped API key.
This uses an admin key that should NEVER be stored in the application.

Usage:
    RESEND_ADMIN_API_KEY=re_full_access_xxx python scripts/create_resend_key.py
"""
import os
import sys
import resend

def main():
    admin_key = os.environ.get("RESEND_ADMIN_API_KEY")
    if not admin_key:
        print("Error: RESEND_ADMIN_API_KEY environment variable not set")
        print("Get your admin key from: https://resend.com/api-keys")
        sys.exit(1)

    resend.api_key = admin_key

    try:
        # Create a sending-only key for the application
        create_params = {
            "name": "fastapi-app-sender",
            "permission": "sending_access"
        }

        created = resend.ApiKeys.create(params=create_params)

        print("✅ API Key created successfully!")
        print("\nAdd this to your .env file:")
        print(f"RESEND_API_KEY={created['token']}")
        print("\n⚠️  This token is shown only once. Store it securely!")

    except Exception as e:
        print(f"Error creating API key: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()