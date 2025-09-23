# tests/test_auth.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import importlib.util
import sys

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
# ----------------- Tests -----------------
def test_hash_password():
    pw = "mysecretpassword"
    hashed = hash_password(pw)
    assert hashed != pw
    assert len(hashed) == 64

def test_is_student_email():
    assert is_student_email("student@uncc.edu")
    assert is_student_email("test@college.edu")
    assert not is_student_email("student@gmail.com")
    assert not is_student_email("invalid-email")
    assert not is_student_email("")

def test_create_and_find_user(db_session):
    email = "testuser@uncc.edu"
    password = "password123"

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
