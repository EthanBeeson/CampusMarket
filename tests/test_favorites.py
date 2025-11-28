import pytest

from app.db import SessionLocal
from app.models.user import User
from app.models.listing import Listing
from app.models.favorite import Favorite
from app.crud.favorites import is_favorited, add_favorite, remove_favorite


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.query(Favorite).delete()
    session.query(Listing).delete()
    session.query(User).delete()
    session.commit()
    session.close()


@pytest.fixture
def user_and_listing(db):
    user = User(email="favtest@charlotte.edu", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)

    listing = Listing(
        title="Test Item",
        description="desc",
        price=10.0,
        condition="Good",
        category="Other",
        user_id=user.id,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return user, listing


def test_favorite_add_remove(db, user_and_listing):
    user, listing = user_and_listing

    assert not is_favorited(db, user.id, listing.id)

    add_favorite(db, user.id, listing.id)
    assert is_favorited(db, user.id, listing.id)

    remove_favorite(db, user.id, listing.id)
    assert not is_favorited(db, user.id, listing.id)


def test_toggle_logic(db, user_and_listing):
    user, listing = user_and_listing

    # First add
    if is_favorited(db, user.id, listing.id):
        remove_favorite(db, user.id, listing.id)
    else:
        add_favorite(db, user.id, listing.id)
    assert is_favorited(db, user.id, listing.id)

    # Then remove
    if is_favorited(db, user.id, listing.id):
        remove_favorite(db, user.id, listing.id)
    else:
        add_favorite(db, user.id, listing.id)
    assert not is_favorited(db, user.id, listing.id)
