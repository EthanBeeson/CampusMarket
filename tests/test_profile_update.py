# tests/test_profile_update.py
"""Tests for updating and removing user profile data, including profile picture.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.crud.users import create_user, update_user_profile, delete_user_profile_picture


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_update_user_profile_fields(db_session):
    user = create_user(db_session, "tester@charlotte.edu", "Password123!")
    # Update fields
    result = update_user_profile(db_session, user_id=user.id, full_name="Test User",
                                 display_name="Tester", phone="+1-555-1234", bio="Hello")
    assert result is True

    refreshed = db_session.query(type(user)).filter(type(user).id == user.id).first()
    assert refreshed.full_name == "Test User"
    assert refreshed.display_name == "Tester"
    assert refreshed.phone == "+1-555-1234"
    assert refreshed.bio == "Hello"


def test_delete_user_profile_picture_clears_field_and_removes_file(db_session, tmp_path):
    user = create_user(db_session, "picuser@charlotte.edu", "Password123!")

    # simulate creating an uploads dir and a profile picture file
    uploads_dir = tmp_path / "uploads" / "profile_pictures"
    uploads_dir.mkdir(parents=True)
    pic_path = uploads_dir / f"profile_{user.id}.png"
    pic_path.write_bytes(b"fakeimagecontent")

    # set the database field to this path
    user.profile_picture = str(pic_path)
    db_session.commit()

    # Now call the delete helper
    result = delete_user_profile_picture(db_session, user.id)
    assert result is True

    # file should be removed
    assert not pic_path.exists()

    refreshed = db_session.query(type(user)).filter(type(user).id == user.id).first()
    assert refreshed.profile_picture is None
