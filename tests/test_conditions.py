import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.user import User
from app.crud.listings import create_listing, update_listing


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_create_listing_with_valid_condition(test_db):
    # create a user to satisfy FK
    user = User(email="u@example.com", hashed_password="x")
    test_db.add(user)
    test_db.commit()

    listing = create_listing(
        test_db,
        title="Test",
        description="Desc",
        price=10.0,
        image_urls=[],
        user_id=user.id,
        condition="Like New",
    )
    assert listing.condition == "Like New"


def test_create_listing_invalid_condition_raises(test_db):
    user = User(email="u2@example.com", hashed_password="x")
    test_db.add(user)
    test_db.commit()

    with pytest.raises(ValueError):
        create_listing(
            test_db,
            title="Bad",
            description="Desc",
            price=5.0,
            image_urls=[],
            user_id=user.id,
            condition="NotACondition",
        )


def test_update_listing_invalid_condition_raises(test_db):
    user = User(email="u3@example.com", hashed_password="x")
    test_db.add(user)
    test_db.commit()

    listing = create_listing(
        test_db,
        title="Up",
        description="Desc",
        price=20.0,
        image_urls=[],
        user_id=user.id,
        condition="Good",
    )

    with pytest.raises(ValueError):
        update_listing(test_db, listing_id=listing.id, condition="TotallyWrong")
