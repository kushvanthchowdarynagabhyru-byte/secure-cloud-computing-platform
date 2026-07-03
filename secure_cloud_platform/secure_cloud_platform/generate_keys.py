"""
Quick helper to generate the two secrets needed in your .env file.
Run: python generate_keys.py
"""
import secrets
from cryptography.fernet import Fernet

print("Copy these into your .env file:\n")
print(f"SECRET_KEY={secrets.token_hex(32)}")
print(f"MASTER_KEY={Fernet.generate_key().decode()}")
