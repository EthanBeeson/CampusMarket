# tests/test_auth.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.crud.users import (
    validate_charlotte_email, 
    validate_password, 
    authenticate_user,
    create_user,
    reset_password_by_email,
    update_user_password,
    verify_user_password,
)
from app.models.user import User
from app.db import Base

# ----------------- Test Setup -----------------
@pytest.fixture
def db_session():
    """Create a fresh database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# ----------------- Email Validation Tests -----------------
def test_validate_charlotte_email():
    """Test Charlotte.edu email validation"""
    # Valid emails
    assert validate_charlotte_email("student@charlotte.edu")[0] == True
    assert validate_charlotte_email("first.last@charlotte.edu")[0] == True
    
    # Invalid emails
    assert validate_charlotte_email("student@gmail.com")[0] == False
    assert validate_charlotte_email("student@uncc.edu")[0] == False
    assert validate_charlotte_email("")[0] == False

def test_charlotte_email_error_messages():
    """Test appropriate error messages for invalid emails"""
    is_valid, error = validate_charlotte_email("student@gmail.com")
    assert is_valid == False
    assert "charlotte.edu" in error.lower()

# ----------------- Password Validation Tests -----------------
def test_validate_password():
    """Test password requirements"""
    # Valid passwords
    assert validate_password("Password123!")[0] == True
    assert validate_password("Test@1234")[0] == True
    
    # Invalid passwords
    assert validate_password("short")[0] == False  # Too short
    assert validate_password("nospecial123")[0] == False  # No special char
    assert validate_password("")[0] == False  # Empty

def test_password_error_messages():
    """Test password error messages"""
    # Test too short
    is_valid, error = validate_password("short")
    assert is_valid == False
    assert "8 characters" in error.lower()
    
    # Test no special char
    is_valid, error = validate_password("nospecial123")
    assert is_valid == False
    assert "special character" in error.lower()

# ----------------- User Creation Tests -----------------
def test_create_user_success(db_session):
    """Test successful user creation"""
    email = "test@charlotte.edu"
    password = "ValidPass123!"
    
    user = create_user(db_session, email, password)
    
    assert user is not None
    assert user.email == email
    assert user.id is not None

def test_create_user_rejects_non_charlotte_email(db_session):
    """Test that user creation rejects non-Charlotte emails"""
    with pytest.raises(ValueError, match="charlotte.edu"):
        create_user(db_session, "invalid@gmail.com", "ValidPass123!")

def test_create_user_rejects_duplicate_email(db_session):
    """Test that duplicate emails are rejected"""
    email = "duplicate@charlotte.edu"
    password = "ValidPass123!"
    
    # Create first user
    create_user(db_session, email, password)
    
    # Try to create duplicate
    with pytest.raises(ValueError, match="already exists"):
        create_user(db_session, email, "DifferentPass123!")

# ----------------- Authentication Tests -----------------
def test_authenticate_user_success(db_session):
    """Test successful authentication"""
    email = "auth@charlotte.edu"
    password = "AuthPass123!"
    
    # Create user first
    create_user(db_session, email, password)
    
    # Test authentication
    is_authenticated, user = authenticate_user(db_session, email, password)
    
    assert is_authenticated == True
    assert user.email == email

def test_authenticate_user_wrong_password(db_session):
    """Test authentication fails with wrong password"""
    email = "test@charlotte.edu"
    password = "CorrectPass123!"
    
    create_user(db_session, email, password)
    
    is_authenticated, user = authenticate_user(db_session, email, "WrongPass123!")
    
    assert is_authenticated == False
    assert user is not None  # User exists but password wrong

def test_authenticate_user_not_found(db_session):
    """Test authentication for non-existent user"""
    is_authenticated, user = authenticate_user(db_session, "nonexistent@charlotte.edu", "AnyPass123!")
    
    assert is_authenticated == False
    assert user is None

def test_authenticate_rejects_non_charlotte_email(db_session):
    """Test authentication rejects non-Charlotte emails"""
    is_authenticated, user = authenticate_user(db_session, "test@gmail.com", "AnyPass123!")
    
    assert is_authenticated == False
    assert user is None

# ----------------- Integration Test -----------------
def test_complete_user_flow(db_session):
    """Test complete user registration and login flow"""
    email = "flow@charlotte.edu"
    password = "FlowPass123!"
    
    # 1. Create user
    user = create_user(db_session, email, password)
    assert user.email == email
    
    # 2. Login with correct credentials
    is_authenticated, logged_in_user = authenticate_user(db_session, email, password)
    assert is_authenticated == True
    assert logged_in_user.id == user.id
    
    # 3. Login with wrong password fails
    is_authenticated, _ = authenticate_user(db_session, email, "WrongPass123!")
    assert is_authenticated == False

# ----------------- Password Reset Tests -----------------
def test_reset_password_success(db_session):
    """Resetting password allows login with new credentials and rejects old."""
    email = "reset@charlotte.edu"
    original_pw = "Original123!"
    new_pw = "NewPass123!"

    user = create_user(db_session, email, original_pw)
    assert user is not None

    assert reset_password_by_email(db_session, email, new_pw) is True

    is_authenticated, _ = authenticate_user(db_session, email, new_pw)
    assert is_authenticated is True

    is_authenticated_old, _ = authenticate_user(db_session, email, original_pw)
    assert is_authenticated_old is False


def test_reset_password_requires_charlotte_email(db_session):
    """Reset should reject non-Charlotte addresses."""
    with pytest.raises(ValueError, match="charlotte.edu"):
        reset_password_by_email(db_session, "person@gmail.com", "ValidPass123!")


def test_reset_password_missing_user(db_session):
    """Reset should raise for unknown accounts."""
    with pytest.raises(ValueError, match="No account"):
        reset_password_by_email(db_session, "missing@charlotte.edu", "ValidPass123!")


def test_reset_password_same_as_old(db_session):
    """Reset should fail if the new password matches the current one."""
    email = "samepw@charlotte.edu"
    password = "Original123!"
    create_user(db_session, email, password)

    with pytest.raises(ValueError, match="different from the current password"):
        reset_password_by_email(db_session, email, password)


def test_update_user_password_success(db_session):
    """Updating password directly should hash and replace the old one."""
    email = "changepw@charlotte.edu"
    original_pw = "Original123!"
    new_pw = "Changed123!"
    user = create_user(db_session, email, original_pw)

    assert verify_user_password(db_session, user.id, original_pw) is True
    assert update_user_password(db_session, user.id, new_pw) is True
    assert verify_user_password(db_session, user.id, new_pw) is True
    assert verify_user_password(db_session, user.id, original_pw) is False


def test_update_user_password_rejects_same(db_session):
    """Direct update should reject setting the same password."""
    email = "samechange@charlotte.edu"
    pw = "Original123!"
    user = create_user(db_session, email, pw)

    with pytest.raises(ValueError, match="different from the current password"):
        update_user_password(db_session, user.id, pw)

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
