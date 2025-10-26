# app/crud/users.py
import hashlib
import re
import os
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


def update_user_profile(db: Session, user_id: int, full_name: str = None, display_name: str = None,
                        phone: str = None, bio: str = None, profile_picture: str = None) -> bool:
    """Update profile fields for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    # --- Server-side validation ---
    # full_name: optional, max 100 chars
    if full_name is not None:
        if not isinstance(full_name, str):
            raise ValueError("Full name must be a string")
        if len(full_name.strip()) > 100:
            raise ValueError("Full name must be 100 characters or fewer.")
        user.full_name = full_name.strip()

    # display_name: optional, max 50 chars
    if display_name is not None:
        if not isinstance(display_name, str):
            raise ValueError("Display name must be a string")
        display_name_clean = display_name.strip()
        if len(display_name_clean) > 50:
            raise ValueError("Display name must be 50 characters or fewer.")
        user.display_name = display_name_clean

    # phone: optional, basic validation
    if phone is not None:
        if not isinstance(phone, str):
            raise ValueError("Phone must be a string")
        phone_clean = phone.strip()
        if phone_clean:
            phone_pattern = r'^\+?[0-9\-\s\(\)]{7,20}$'
            if not re.match(phone_pattern, phone_clean):
                raise ValueError("Phone number appears invalid.")
        user.phone = phone_clean

    # bio: optional, max 500 chars
    if bio is not None:
        if not isinstance(bio, str):
            raise ValueError("Bio must be a string")
        bio_clean = bio.strip()
        if len(bio_clean) > 500:
            raise ValueError("Bio must be 500 characters or fewer.")
        user.bio = bio_clean

    # profile_picture: optional, must be a path string
    if profile_picture is not None:
        if not isinstance(profile_picture, str):
            raise ValueError("Profile picture path must be a string")
        if len(profile_picture) > 255:
            raise ValueError("Profile picture path too long")
        user.profile_picture = profile_picture

    db.commit()
    db.refresh(user)
    return True


def delete_user_profile_picture(db: Session, user_id: int) -> bool:
    """Remove profile picture file from disk and clear profile_picture DB field.

    Returns True on success, False if user not found.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    pic_path = getattr(user, "profile_picture", None)
    if pic_path:
        try:
            if os.path.exists(pic_path):
                os.remove(pic_path)
        except OSError:
            # ignore file removal errors but continue to clear DB
            pass

    user.profile_picture = None
    db.commit()
    db.refresh(user)
    return True