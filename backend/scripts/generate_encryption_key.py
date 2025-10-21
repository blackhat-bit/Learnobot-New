#!/usr/bin/env python3
"""
Generate encryption key for API key storage.
Run this script ONCE to generate a key, then add it to your .env file.
"""
from cryptography.fernet import Fernet

def main():
    # Generate a new Fernet key
    key = Fernet.generate_key()
    
    print("\n" + "="*60)
    print("🔐 ENCRYPTION KEY GENERATED")
    print("="*60)
    print("\nAdd this line to your .env file:")
    print(f"\nENCRYPTION_KEY={key.decode()}")
    print("\n" + "="*60)
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("="*60)
    print("1. Keep this key SECRET - never commit it to version control")
    print("2. Store it securely (e.g., password manager, secure vault)")
    print("3. Without this key, you CANNOT decrypt stored API keys")
    print("4. If you lose this key, you'll need to re-enter all API keys")
    print("5. Use the same key across all environments to migrate data")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

