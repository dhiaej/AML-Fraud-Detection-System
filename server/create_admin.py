"""
Script to create a default admin account
"""
import sys
from pathlib import Path

# Add parent directory to path
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

from src.database.sqlite_connector import SQLiteConnector
import hashlib

def hash_password(password: str) -> str:
    """Simple password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin():
    db = SQLiteConnector()
    
    # Default admin credentials
    email = "admin@admin.com"
    password = "admin123"
    name = "System Administrator"
    user_id = "ADMIN001"
    
    # Check if admin already exists
    existing = db.get_auth_user_by_email(email)
    if existing:
        print(f"Admin account already exists!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        return
    
    # Create user in users table
    try:
        db.add_user(
            user_id=user_id,
            name=name,
            risk_score=0.1,
            account_age_days=365
        )
    except Exception as e:
        print(f"Note: User might already exist: {e}")
    
    # Create auth user
    password_hash = hash_password(password)
    
    db.create_auth_user(
        email=email,
        password_hash=password_hash,
        user_id=user_id,
        role="admin"
    )
    
    print("=" * 50)
    print("Admin Account Created Successfully!")
    print("=" * 50)
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print(f"Role:    admin")
    print("=" * 50)
    print("\nYou can now login with these credentials.")

if __name__ == "__main__":
    create_admin()
