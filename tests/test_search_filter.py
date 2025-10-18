import pytest
from app.db import Base, engine, SessionLocal
from app.models.listing import Listing
from app.crud.listings import search_listings

# ----------- TEST SETUP ------------ #

@pytest.fixture(scope="module")
def db():
    """Set up a temporary database for testing."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clean and seed test data
    db.query(Listing).delete()

    listings = [
        Listing(title="Mountain Bike", description="Used bicycle, good condition", price=150.0),
        Listing(title="Road Bicycle", description="Lightweight frame", price=300.0),
        Listing(title="Gaming Laptop", description="RTX 4060, 16GB RAM", price=1200.0),
        Listing(title="Desk Chair", description="Ergonomic and comfortable", price=100.0),
    ]
    db.add_all(listings)
    db.commit()
    yield db

    # Teardown
    db.query(Listing).delete()
    db.commit()
    db.close()


# ----------- TESTS BEGIN HERE ------------ #

def test_fuzzy_keyword_match(db):
    """Ensure fuzzy search returns close matches (case-insensitive)."""
    results = search_listings(db, keyword="bike", threshold=50)
    titles = [l.title for l in results]

    assert any("Bike" in t or "Bicycle" in t for t in titles)
    assert all(isinstance(l, Listing) for l in results)


def test_exact_keyword_match(db):
    """Test exact matching returns expected results."""
    results = search_listings(db, keyword="Gaming Laptop")
    assert len(results) == 1
    assert results[0].title == "Gaming Laptop"


def test_price_filter_min(db):
    """Ensure listings below min_price are excluded."""
    results = search_listings(db, keyword="", min_price=200.0)
    for l in results:
        assert l.price >= 200.0


def test_price_filter_max(db):
    """Ensure listings above max_price are excluded."""
    results = search_listings(db, keyword="", max_price=300.0)
    for l in results:
        assert l.price <= 300.0


def test_combined_keyword_and_price(db):
    """Ensure fuzzy search and price filters both apply."""
    results = search_listings(db, keyword="bike", threshold=60, min_price=100.0, max_price=200.0)
    assert all(100.0 <= l.price <= 200.0 for l in results)
    assert any("Bike" in l.title or "Bicycle" in l.title for l in results)


def test_no_results(db):
    """Return empty list if no matches are found."""
    results = search_listings(db, keyword="spaceship")
    assert results == []
