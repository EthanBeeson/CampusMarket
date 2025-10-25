# app/crud/users.py
import hashlib
import re
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User

def hash_password(password: str) -> str:
    """Return SHA-256 hash of password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password meets requirements:
    - At least 8 characters
    - At least 1 special character
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    # Check for at least one special character
    special_char_pattern = r'[!@#$%^&*(),.?":{}|<>]'
    if not re.search(special_char_pattern, password):
        return False, "Password must contain at least one special character."
    
    return True, ""

def validate_charlotte_email(email: str) -> tuple[bool, str]:
    """
    Validate email is a Charlotte student email.
    Returns (is_valid, error_message)
    """
    if not email.strip():
        return False, "Email cannot be empty."
    
    # Check for @charlotte.edu domain
    if not email.lower().endswith('@charlotte.edu'):
        return False, "Only @charlotte.edu email addresses are allowed."
    
    return True, ""

def create_user(db: Session, email: str, password: str) -> User:
    """
    Create a new user with validation.
    Raises ValueError if validation fails.
    """
    # Validate email
    is_valid_email, email_error = validate_charlotte_email(email)
    if not is_valid_email:
        raise ValueError(email_error)
    
    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        raise ValueError(password_error)
    
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise ValueError("An account with this email already exists.")
    
    # Create user
    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> User:
    """Get user by email address."""
    stmt = select(User).where(User.email == email.lower().strip())
    return db.execute(stmt).scalars().first()

def authenticate_user(db: Session, email: str, password: str) -> tuple[bool, User]:
    """
    Authenticate user with email and password.
    Returns (is_authenticated, user_object)
    """
    user = get_user_by_email(db, email)
    if not user:
        return False, None
    
    if user.hashed_password == hash_password(password):
        return True, user
    else:
        return False, user

def update_user_password(db: Session, user_id: int, new_password: str) -> bool:
    """
    Update user password with validation.
    Returns True if successful, False otherwise.
    """
    # Validate new password
    is_valid, error_message = validate_password(new_password)
    if not is_valid:
        raise ValueError(error_message)
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.hashed_password = hash_password(new_password)
        db.commit()
        return True
    return False