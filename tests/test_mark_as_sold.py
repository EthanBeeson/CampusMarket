import uuid
import pytest

from app.db import Base, engine, SessionLocal
from app.models.user import User
from app.models.listing import Listing
from app.crud.listings import mark_listing_sold, ForbiddenAction

# ----------- TEST SETUP (mirror partner style) ------------ #

@pytest.fixture(scope="module")
def db():
    """Use app engine/SessionLocal; create tables and seed one module-scoped DB."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    # Clean slate for this module
    session.query(Listing).delete()
    session.query(User).delete()
    session.commit()

    try:
        yield session
    finally:
        # Teardown for this module
        session.query(Listing).delete()
        session.query(User).delete()
        session.commit()
        session.close()

def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@charlotte.edu"  # short unique suffix

@pytest.fixture()
def owner(db):
    """Owner user fixture."""
    u = User(email=unique_email("owner"), hashed_password="x")  # unique email
    db.add(u); db.commit(); db.refresh(u)
    return u

@pytest.fixture()
def other_user(db):
    """Non-owner user fixture."""
    u = User(email=unique_email("viewer"), hashed_password="x")  # unique email
    db.add(u); db.commit(); db.refresh(u)
    return u

@pytest.fixture()
def listing(db, owner):
    """Fresh listing owned by `owner` for each test."""
    l = Listing(
        title="Mini Fridge",
        description="Works well",
        price=100.0,
        condition="Good",
        user_id=owner.id,    # <-- user_id added
        is_sold=False,
    )
    db.add(l); db.commit(); db.refresh(l)
    try:
        yield l
    finally:
        # Remove if still present
        if db.get(Listing, l.id):
            db.delete(l); db.commit()

# ----------- TESTS (Story #7) ------------ #

def test_mark_sold_as_owner_sets_flag(db, listing, owner):
    ok = mark_listing_sold(db, listing_id=listing.id, user_id=owner.id)
    assert ok is True
    db.refresh(listing)
    assert listing.is_sold is True

def test_mark_sold_by_non_owner_raises(db, listing, other_user):
    with pytest.raises(ForbiddenAction):
        mark_listing_sold(db, listing_id=listing.id, user_id=other_user.id)

def test_mark_sold_not_found_returns_false(db, owner):
    ok = mark_listing_sold(db, listing_id=123456789, user_id=owner.id)
    assert ok is False
