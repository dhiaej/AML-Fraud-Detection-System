"""
Authentication Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import secrets
from ..database.sqlite_connector import SQLiteConnector

router = APIRouter()
db = SQLiteConnector()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    email: str
    user_id: Optional[str]
    role: str
    name: Optional[str] = None


def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    """Generate a simple token (use JWT in production)."""
    return secrets.token_urlsafe(32)


@router.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest):
    """Sign up a new user."""
    # Check if email already exists
    existing = db.get_auth_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate user_id if not provided
    user_id = request.user_id
    if not user_id:
        # Generate a user_id
        users = db.get_all_users()
        user_id = f"U{len(users) + 1:03d}"
    
    # Create user in users table
    try:
        db.add_user(
            user_id=user_id,
            name=request.name,
            risk_score=0.5,
            account_age_days=0
        )
    except Exception:
        pass  # User might already exist
    
    # Create auth user
    password_hash = hash_password(request.password)
    role = "admin" if request.email.endswith("@admin.com") else "user"
    
    db.create_auth_user(
        email=request.email,
        password_hash=password_hash,
        user_id=user_id,
        role=role
    )
    
    token = generate_token()
    
    return AuthResponse(
        token=token,
        email=request.email,
        user_id=user_id,
        role=role,
        name=request.name
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest):
    """Login user."""
    auth_user = db.get_auth_user_by_email(request.email)
    if not auth_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    password_hash = hash_password(request.password)
    if auth_user['password_hash'] != password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Get user info
    user = None
    if auth_user.get('user_id'):
        user = db.get_user_by_id(auth_user['user_id'])
    
    token = generate_token()
    
    return AuthResponse(
        token=token,
        email=request.email,
        user_id=auth_user.get('user_id'),
        role=auth_user.get('role', 'user'),
        name=user.get('name') if user else None
    )
