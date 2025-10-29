import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.listing import Listing
from app.models.image import Image
from app.models.user import User
from app.crud.listings import create_listing, get_listings, delete_listing

# --- Setup in-memory test database ---

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

# --- helper: ensure we always have an owner user for NOT NULL listings.user_id ---
def _ensure_user(db):
    u = db.query(User).filter_by(email="test_owner@charlotte.edu").first()
    if not u:
        u = User(email="test_owner@charlotte.edu", hashed_password="x")
        db.add(u); db.commit(); db.refresh(u)
    return u

# --- 1. Test create_listing works correctly ---
def test_create_listing(test_db):
    listing = create_listing(
        test_db,
        title="Test Item",
        description="This is a test listing.",
        price=50.0,
        image_urls=["test1.jpg", "test2.jpg"],
        user_id=_ensure_user(test_db).id,  # <-- added
    )
    assert listing.id is not None
    assert len(listing.images) == 2
    assert listing.title == "Test Item"

# --- 2. Test get_listings returns persisted data ---
def test_get_listings_persistence(test_db):
    create_listing(
        test_db,
        title="Laptop",
        description="Good laptop",
        price=400.0,
        image_urls=["laptop.jpg"],
        user_id=_ensure_user(test_db).id,  # <-- added
    )
    listings = get_listings(test_db)
    assert len(listings) == 1
    assert listings[0].title == "Laptop"

# --- 3. Test duplicate entries allowed ---
def test_duplicate_entries(test_db):
    create_listing(test_db, "Chair", "Nice chair", 20.0, [], user_id=_ensure_user(test_db).id)  # <-- added
    create_listing(test_db, "Chair", "Nice chair", 20.0, [], user_id=_ensure_user(test_db).id)  # <-- added
    listings = get_listings(test_db)
    assert len(listings) == 2

# --- 4. Test invalid schema / missing fields ---
def test_invalid_listing_missing_field(test_db):
    with pytest.raises(TypeError):
        # Missing required argument `title`
        create_listing(
            test_db,
            description="Missing title",
            price=10.0,
            image_urls=[],
            user_id=_ensure_user(test_db).id,  # <-- added (still missing title -> TypeError)
        )

# --- 5. Test price constraint (e.g., cannot be negative) ---
def test_invalid_price_constraint(test_db):
    with pytest.raises(Exception):
        create_listing(
            test_db,
            "Broken Item",
            "Invalid price",
            -10.0,
            [],
            user_id=_ensure_user(test_db).id,  # <-- added
        )

# --- 6. Test delete_listing removes record and cascades images ---
def test_delete_listing(test_db):
    listing = create_listing(
        test_db,
        "Old Phone",
        "Works fine",
        100.0,
        ["phone1.jpg", "phone2.jpg"],
        user_id=_ensure_user(test_db).id,  # <-- added
    )
    deleted = delete_listing(test_db, listing.id)
    assert deleted is True

    listings = get_listings(test_db)
    assert len(listings) == 0

    images = test_db.query(Image).all()
    assert len(images) == 0  # images cascade deleted

# --- 7. Test deleting non-existent listing ---
def test_delete_nonexistent_listing(test_db):
    deleted = delete_listing(test_db, 999)
    assert deleted is False
