# tests/test_auth.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import importlib.util
import sys
import re

# Dynamic import of the login module
def import_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

login_module = import_module_from_path("login_module", "app/pages/2_Login.py")

User = login_module.User
hash_password = login_module.hash_password
is_student_email = login_module.is_student_email
find_user_by_email = login_module.find_user_by_email
create_user = login_module.create_user
ORMBase = login_module.ORMBase

# Import the new CRUD functions for testing
from app.crud.users import (
    validate_charlotte_email,
    validate_password,
    authenticate_user
)

# ----------------- Pytest fixture: fresh in-memory DB -----------------
@pytest.fixture
def db_session():
    # Create a fresh in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Make sure all tables from ORMBase are created in THIS engine
    ORMBase.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Test Data for new validation tests
VALID_CHARLOTTE_EMAILS = [
    "student@charlotte.edu",
    "first.last@charlotte.edu",
    "first_last@charlotte.edu",
    "f.last@charlotte.edu",
    "first1.last2@charlotte.edu"
]

INVALID_EMAILS = [
    "student@gmail.com",
    "student@uncc.edu",  # Should now be rejected
    "student@charlotte.com",
    "student@charlotte.org",
    "student@other.edu",
    "invalid-email",
    "@charlotte.edu",
    "student@",
    "",
    "   "
]

VALID_PASSWORDS = [
    "Password123!",
    "SecurePass#2024",
    "Test@1234",
    "Charlotte$1"
]

INVALID_PASSWORDS = [
    "short1!",
    "nopass",
    "NoSpecialChar123",
    "Abc123",
    "",
    "    "
]

# ----------------- Existing Tests (Keep these) -----------------
def test_hash_password():
    pw = "mysecretpassword"
    hashed = hash_password(pw)
    assert hashed != pw
    assert len(hashed) == 64

def test_is_student_email():
    # Update this test to reflect new Charlotte.edu requirement
    assert is_student_email("student@charlotte.edu")
    assert is_student_email("test@charlotte.edu")
    assert not is_student_email("student@uncc.edu")  # Should now fail
    assert not is_student_email("student@gmail.com")
    assert not is_student_email("invalid-email")
    assert not is_student_email("")

def test_create_and_find_user(db_session):
    email = "testuser@charlotte.edu"  # Updated to charlotte.edu
    password = "ValidPass123!"  # Updated to meet new requirements

    # User should not exist yet
    assert find_user_by_email(db_session, email) is None

    # Create user
    user = create_user(db_session, email, password)
    assert user.id is not None
    assert user.email == email
    assert user.password_hash == hash_password(password)

    # Now user should exist
    fetched_user = find_user_by_email(db_session, email)
    assert fetched_user.id == user.id
    assert fetched_user.email == user.email

# ----------------- New Tests for Charlotte.edu Validation -----------------
class TestCharlotteEmailValidation:
    """Test the new @charlotte.edu email requirement"""
    
    def test_valid_charlotte_emails(self):
        """Test that valid @charlotte.edu emails pass validation"""
        for email in VALID_CHARLOTTE_EMAILS:
            is_valid, error = validate_charlotte_email(email)
            assert is_valid == True, f"Expected {email} to be valid, but got error: {error}"
            assert error == "", f"Expected no error for {email}, but got: {error}"
    
    def test_invalid_email_domains_rejected(self):
        """Test that non-@charlotte.edu emails are rejected"""
        for email in INVALID_EMAILS:
            is_valid, error = validate_charlotte_email(email)
            assert is_valid == False, f"Expected {email} to be invalid, but it passed"
            assert "charlotte.edu" in error.lower(), f"Error message should mention charlotte.edu for {email}"
    
    def test_email_case_insensitive(self):
        """Test that email validation is case insensitive"""
        mixed_case_emails = [
            "Student@CHARLOTTE.EDU",
            "FIRST.LAST@Charlotte.Edu",
            "Mixed.Case@CHARLOTTE.edu"
        ]
        
        for email in mixed_case_emails:
            is_valid, error = validate_charlotte_email(email)
            assert is_valid == True, f"Case insensitive validation failed for {email}"
    
    def test_legacy_is_student_email_compatibility(self):
        """Test that the legacy function still works but with new domain"""
        # These should work with both old and new systems
        assert is_student_email("test@charlotte.edu")
        assert is_student_email("user@charlotte.edu")
        
        # These should fail with new system
        assert not is_student_email("test@uncc.edu")
        assert not is_student_email("test@gmail.com")

# ----------------- New Tests for Password Validation -----------------
class TestPasswordValidation:
    """Test the new password requirements (8+ chars, 1 special char)"""
    
    def test_valid_passwords(self):
        """Test that valid passwords pass validation"""
        for password in VALID_PASSWORDS:
            is_valid, error = validate_password(password)
            assert is_valid == True, f"Expected password to be valid, but got error: {error}"
            assert error == "", f"Expected no error for password, but got: {error}"
    
    def test_invalid_passwords_rejected(self):
        """Test that invalid passwords are rejected with appropriate errors"""
        test_cases = [
            ("short1!", "at least 8 characters"),
            ("nopass", "at least 8 characters"),
            ("NoSpecialChar123", "special character"),
            ("Abc123", "at least 8 characters"),
            ("", "at least 8 characters"),
        ]
        
        for password, expected_error in test_cases:
            is_valid, error = validate_password(password)
            assert is_valid == False, f"Expected {password} to be invalid"
            assert expected_error in error.lower(), f"Error '{error}' should contain '{expected_error}' for password '{password}'"
    
    def test_password_special_characters_accepted(self):
        """Test various special characters are accepted"""
        special_char_passwords = [
            "Test123!",
            "Test123@",
            "Test123#",
            "Test123$",
            "Test123%",
        ]
        
        for password in special_char_passwords:
            is_valid, error = validate_password(password)
            assert is_valid == True, f"Password with special char should be valid: {password}, error: {error}"

# ----------------- New Tests for User Creation with Validation -----------------
class TestUserCreationWithValidation:
    """Test user creation with the new validation requirements"""
    
    def test_create_user_with_valid_charlotte_email(self, db_session):
        """Test creating a user with valid charlotte.edu email"""
        email = "new.student@charlotte.edu"
        password = "ValidPass123!"
        
        user = create_user(db_session, email, password)
        
        assert user is not None
        assert user.email == email
        assert user.password_hash == hash_password(password)
    
    def test_create_user_rejects_non_charlotte_email(self, db_session):
        """Test that user creation rejects non-charlotte.edu emails"""
        invalid_emails = ["test@gmail.com", "test@uncc.edu", "invalid-email"]
        password = "ValidPass123!"
        
        for email in invalid_emails:
            try:
                create_user(db_session, email, password)
                assert False, f"Should have raised ValueError for {email}"
            except ValueError as e:
                assert "charlotte.edu" in str(e).lower()
    
    def test_create_user_rejects_weak_password(self, db_session):
        """Test that user creation rejects weak passwords"""
        email = "test.student@charlotte.edu"
        weak_passwords = ["short1!", "nospchar123", "Abc123"]
        
        for password in weak_passwords:
            try:
                create_user(db_session, email, password)
                assert False, f"Should have raised ValueError for weak password: {password}"
            except ValueError as e:
                assert "password" in str(e).lower()

# ----------------- New Tests for Authentication -----------------
class TestUserAuthentication:
    """Test user authentication with new requirements"""
    
    def test_authenticate_valid_user(self, db_session):
        """Test successful authentication with valid credentials"""
        email = "auth.test@charlotte.edu"
        password = "AuthPass123!"
        
        # Create user first
        create_user(db_session, email, password)
        
        # Test authentication
        is_authenticated, user = authenticate_user(db_session, email, password)
        
        assert is_authenticated == True
        assert user is not None
        assert user.email == email
    
    def test_authenticate_invalid_password(self, db_session):
        """Test authentication fails with wrong password"""
        email = "auth.test@charlotte.edu"
        password = "CorrectPass123!"
        
        # Create user
        create_user(db_session, email, password)
        
        # Test with wrong password
        is_authenticated, user = authenticate_user(db_session, email, "WrongPass123!")
        
        assert is_authenticated == False
        assert user is not None  # User exists, but password is wrong
    
    def test_authenticate_rejects_non_charlotte_email(self, db_session):
        """Test authentication rejects non-charlotte.edu emails"""
        is_authenticated, user = authenticate_user(db_session, "test@gmail.com", "AnyPass123!")
        
        assert is_authenticated == False
        assert user is None

# ----------------- Integration Tests -----------------
class TestIntegrationScenarios:
    """Test complete user registration and login scenarios with new requirements"""
    
    def test_complete_flow_with_new_requirements(self, db_session):
        """Test the complete flow with Charlotte.edu and password requirements"""
        # Registration with valid credentials
        email = "integration.test@charlotte.edu"
        password = "Integration123!"
        
        user = create_user(db_session, email, password)
        assert user is not None
        
        # Login with same credentials
        is_authenticated, logged_in_user = authenticate_user(db_session, email, password)
        assert is_authenticated == True
        assert logged_in_user.id == user.id
        
        # Verify cannot login with wrong password
        is_authenticated, _ = authenticate_user(db_session, email, "WrongPass123!")
        assert is_authenticated == False
    
    def test_backward_compatibility_check(self, db_session):
        """Test that old @uncc.edu emails are no longer accepted"""
        try:
            create_user(db_session, "olduser@uncc.edu", "Password123!")
            assert False, "Should have rejected @uncc.edu email"
        except ValueError as e:
            assert "charlotte.edu" in str(e).lower()

# Run specific test groups
if __name__ == "__main__":
    # You can run specific test classes like this:
    # pytest tests/test_auth.py::TestCharlotteEmailValidation -v
    # pytest tests/test_auth.py::TestPasswordValidation -v
    # pytest tests/test_auth.py::TestUserCreationWithValidation -v
    pytest.main([__file__, "-v"])