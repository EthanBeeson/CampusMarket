# tests/test_edit_delete.py
import uuid  # <-- add
import pytest
from app.db import Base, engine, SessionLocal
from app.models.user import User
from app.models.listing import Listing
from app.crud.listings import update_listing, delete_listing

# ----------- TEST SETUP (mirror partner style) ------------ #

@pytest.fixture(scope="module")
def db():
    """Use app engine/SessionLocal; create tables and seed one module-scoped DB."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    # Clean slate
    session.query(Listing).delete()
    session.query(User).delete()
    session.commit()

    try:
        yield session
    finally:
        # If a previous test blew up, the session may be in a failed state
        try:
            session.rollback()
        except Exception:
            pass
        # Teardown: clean what we created
        session.query(Listing).delete()
        session.query(User).delete()
        session.commit()
        session.close()

def _unique_email(prefix="edit_owner"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@charlotte.edu"  # <-- unique per test

@pytest.fixture()
def owner(db):
    """Create an owner user for listings."""
    u = User(email=_unique_email(), hashed_password="x")  # <-- unique email
    db.add(u); db.commit(); db.refresh(u)
    return u

@pytest.fixture()
def one_listing(db, owner):
    """Return a fresh listing to edit/delete each test (insert, yield, then delete)."""
    l = Listing(title="Temp Item", description="temp", price=50.0, condition="Good", user_id=owner.id)
    db.add(l); db.commit(); db.refresh(l)
    try:
        yield l
    finally:
        # remove if still present
        if db.get(Listing, l.id):
            db.delete(l); db.commit()

# ----------- TESTS (#75 Edit) ------------ #

def test_edit_listing_updates_all_fields(db, one_listing):
    updated = update_listing(
        db,
        listing_id=one_listing.id,
        title="Temp Item (Edited)",
        description="Updated description",
        price=75.0,
        condition="New",
    )
    # ensure we’re looking at the committed row
    db.refresh(updated)
    reloaded = db.get(Listing, one_listing.id)

    assert reloaded is not None
    assert reloaded.title == "Temp Item (Edited)"
    assert reloaded.description == "Updated description"
    assert reloaded.price == 75.0
    assert reloaded.condition == "New"

def test_edit_listing_partial_update_keeps_others(db, one_listing):
    before = db.get(Listing, one_listing.id)
    updated = update_listing(db, listing_id=one_listing.id, price=60.0)
    db.refresh(updated)
    after = db.get(Listing, one_listing.id)

    assert after.price == 60.0
    # unchanged fields remain
    assert after.title == before.title
    assert after.description == before.description
    assert after.condition == before.condition

def test_edit_listing_rejects_negative_price(db, one_listing):
    with pytest.raises(ValueError):
        update_listing(db, listing_id=one_listing.id, price=-1.0)

# ----------- TESTS (#79 Delete) ------------ #

def test_delete_listing_success(db, one_listing):
    ok = delete_listing(db, listing_id=one_listing.id)
    assert ok is True
    assert db.get(Listing, one_listing.id) is None

def test_delete_listing_not_found(db):
    ok = delete_listing(db, listing_id=999_999_999)
    assert ok is False
