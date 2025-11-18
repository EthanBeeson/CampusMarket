# tests/test_public_profile.py
"""
Tests for the public profile page (pages/5_Public_Profile.py).
This module tests the functionality of displaying user profiles, listings, and reviews.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.crud.users import create_user
from app.crud.listings import create_listing
from app.crud.reviews import create_review, get_reviews_for_user, get_user_average_rating
from app.models.user import User
from app.models.listing import Listing
from app.models.review import Review
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

@pytest.fixture
def profile_user(db_session):
    """Create a user whose profile we'll test"""
    user = create_user(db_session, "profile@charlotte.edu", "Password123!")
    user.full_name = "John Seller"
    user.display_name = "JohnS"
    user.bio = "College student selling textbooks"
    db_session.commit()
    return user

@pytest.fixture
def other_users(db_session):
    """Create other users for testing reviews"""
    user1 = create_user(db_session, "buyer1@charlotte.edu", "Password123!")
    user2 = create_user(db_session, "buyer2@charlotte.edu", "Password123!")
    return {"buyer1": user1, "buyer2": user2}

@pytest.fixture
def profile_listings(db_session, profile_user):
    """Create listings for the profile user"""
    listing1 = create_listing(
        db_session,
        title="Biology Textbook",
        description="Used Biology textbook, great condition",
        price=45.00,
        image_urls=[],
        user_id=profile_user.id,
        condition="Good",
        category="Books",
        contact_email="profile@charlotte.edu"
    )
    listing2 = create_listing(
        db_session,
        title="Laptop Stand",
        description="Metal laptop stand",
        price=20.00,
        image_urls=[],
        user_id=profile_user.id,
        condition="Like New",
        category="Electronics",
        contact_email="profile@charlotte.edu"
    )
    return [listing1, listing2]

@pytest.fixture
def profile_reviews(db_session, profile_user, other_users):
    """Create reviews for the profile user"""
    review1 = create_review(
        db_session,
        reviewer_id=other_users["buyer1"].id,
        reviewed_user_id=profile_user.id,
        rating=5.0,
        comment="Excellent seller, very responsive!"
    )
    review2 = create_review(
        db_session,
        reviewer_id=other_users["buyer2"].id,
        reviewed_user_id=profile_user.id,
        rating=4.0,
        comment="Good condition item as described"
    )
    return [review1, review2]

# ----------------- User Profile Display Tests -----------------
def test_profile_user_basic_info(db_session, profile_user):
    """Test that profile user has basic information"""
    user = db_session.query(User).filter(User.id == profile_user.id).first()
    
    assert user is not None
    assert user.email == "profile@charlotte.edu"
    assert user.full_name == "John Seller"
    assert user.display_name == "JohnS"
    assert user.bio == "College student selling textbooks"

def test_profile_user_has_display_name_fallback(db_session):
    """Test that profile falls back to full_name if display_name is None"""
    user = create_user(db_session, "fallback@charlotte.edu", "Password123!")
    user.full_name = "Fallback User"
    user.display_name = None
    db_session.commit()
    
    retrieved = db_session.query(User).filter(User.id == user.id).first()
    display_name = retrieved.display_name or retrieved.full_name or f"User {retrieved.id}"
    
    assert display_name == "Fallback User"

def test_profile_user_no_name_fallback(db_session):
    """Test that profile uses user ID if no display_name or full_name"""
    user = create_user(db_session, "noname@charlotte.edu", "Password123!")
    user.full_name = None
    user.display_name = None
    db_session.commit()
    
    retrieved = db_session.query(User).filter(User.id == user.id).first()
    display_name = retrieved.display_name or retrieved.full_name or f"User {retrieved.id}"
    
    assert display_name == f"User {user.id}"

# ----------------- Profile User Average Rating Tests -----------------
def test_profile_user_average_rating(db_session, profile_user, profile_reviews):
    """Test average rating calculation for profile"""
    avg_rating = get_user_average_rating(db_session, profile_user.id)
    
    # Average of 5.0 and 4.0 = 4.5
    assert avg_rating == 4.5

def test_profile_user_no_reviews_rating(db_session, profile_user):
    """Test that user with no reviews has no average rating"""
    avg_rating = get_user_average_rating(db_session, profile_user.id)
    
    assert avg_rating is None

def test_profile_user_single_review_rating(db_session, profile_user, other_users):
    """Test average rating with single review"""
    create_review(
        db_session,
        reviewer_id=other_users["buyer1"].id,
        reviewed_user_id=profile_user.id,
        rating=3.5
    )
    
    avg_rating = get_user_average_rating(db_session, profile_user.id)
    
    assert avg_rating == 3.5

# ----------------- Profile Listings Display Tests -----------------
def test_profile_listings_retrieval(db_session, profile_user, profile_listings):
    """Test retrieving all listings for profile user"""
    listings = db_session.query(Listing).filter(Listing.user_id == profile_user.id).all()
    
    assert len(listings) == 2
    assert all(l.user_id == profile_user.id for l in listings)

def test_profile_listings_have_required_fields(db_session, profile_user, profile_listings):
    """Test that profile listings have all required display fields"""
    listings = db_session.query(Listing).filter(Listing.user_id == profile_user.id).all()
    
    for listing in listings:
        assert listing.title is not None
        assert listing.description is not None
        assert listing.price is not None
        assert listing.condition is not None
        assert listing.category is not None

def test_profile_listings_count(db_session, profile_user, profile_listings):
    """Test listing count for profile"""
    count = db_session.query(Listing).filter(Listing.user_id == profile_user.id).count()
    
    assert count == 2

def test_profile_user_no_listings(db_session):
    """Test profile with no listings"""
    user = create_user(db_session, "nolisting@charlotte.edu", "Password123!")
    
    listings = db_session.query(Listing).filter(Listing.user_id == user.id).all()
    
    assert len(listings) == 0

# ----------------- Profile Reviews Display Tests -----------------
def test_profile_reviews_retrieval(db_session, profile_user, profile_reviews):
    """Test retrieving reviews for profile user"""
    reviews = get_reviews_for_user(db_session, profile_user.id)
    
    assert len(reviews) == 2
    assert all(r.reviewed_user_id == profile_user.id for r in reviews)

def test_profile_reviews_have_reviewer_info(db_session, profile_user, profile_reviews):
    """Test that reviews include reviewer information"""
    reviews = get_reviews_for_user(db_session, profile_user.id)
    
    for review in reviews:
        assert review.reviewer is not None
        assert review.reviewer_id is not None

def test_profile_reviews_have_content(db_session, profile_user, profile_reviews):
    """Test that reviews have rating and optional comment"""
    reviews = get_reviews_for_user(db_session, profile_user.id)
    
    for review in reviews:
        assert review.rating is not None
        assert review.created_at is not None
        # Comment may be None but that's okay

def test_profile_reviews_no_reviews(db_session):
    """Test profile with no reviews"""
    user = create_user(db_session, "noreviews@charlotte.edu", "Password123!")
    
    reviews = get_reviews_for_user(db_session, user.id)
    
    assert len(reviews) == 0

# ----------------- User Query by ID Tests -----------------
def test_query_profile_user_by_id(db_session, profile_user):
    """Test querying profile user by ID"""
    user = db_session.query(User).filter(User.id == profile_user.id).first()
    
    assert user is not None
    assert user.id == profile_user.id
    assert user.email == "profile@charlotte.edu"

def test_query_nonexistent_user(db_session):
    """Test querying non-existent user returns None"""
    user = db_session.query(User).filter(User.id == 9999).first()
    
    assert user is None

def test_query_user_includes_relationships(db_session, profile_user, profile_listings, profile_reviews):
    """Test that queried user has access to related data"""
    user = db_session.query(User).filter(User.id == profile_user.id).first()
    
    # Check listings relationship
    listings = db_session.query(Listing).filter(Listing.user_id == user.id).all()
    assert len(listings) == 2
    
    # Check reviews relationship
    reviews = db_session.query(Review).filter(Review.reviewed_user_id == user.id).all()
    assert len(reviews) == 2

# ----------------- Integration Tests -----------------
def test_complete_profile_display_flow(db_session, profile_user, other_users):
    """Test complete user profile display workflow"""
    # 1. Create user with info
    user = profile_user
    assert user.email == "profile@charlotte.edu"
    
    # 2. Create listings
    listing1 = create_listing(
        db_session,
        title="Item 1",
        description="Description 1",
        price=10.0,
        image_urls=[],
        user_id=user.id,
        condition="Good",
        category="Books",
        contact_email="profile@charlotte.edu"
    )
    listing2 = create_listing(
        db_session,
        title="Item 2",
        description="Description 2",
        price=20.0,
        image_urls=[],
        user_id=user.id,
        condition="Like New",
        category="Electronics",
        contact_email="profile@charlotte.edu"
    )
    
    user_listings = db_session.query(Listing).filter(Listing.user_id == user.id).all()
    assert len(user_listings) == 2
    
    # 3. Create reviews
    review1 = create_review(
        db_session, other_users["buyer1"].id, user.id, 5.0, "Great!"
    )
    review2 = create_review(
        db_session, other_users["buyer2"].id, user.id, 4.0, "Good"
    )
    
    user_reviews = get_reviews_for_user(db_session, user.id)
    assert len(user_reviews) == 2
    
    # 4. Check average rating
    avg_rating = get_user_average_rating(db_session, user.id)
    assert avg_rating == 4.5

def test_profile_data_isolation(db_session, profile_user, other_users):
    """Test that profile data doesn't leak between users"""
    # Create listings for profile user
    listing1 = create_listing(
        db_session,
        title="Profile Item",
        description="Description",
        price=10.0,
        image_urls=[],
        user_id=profile_user.id,
        condition="Good",
        category="Books",
        contact_email="profile@charlotte.edu"
    )
    
    # Create listings for other user
    other_user = other_users["buyer1"]
    listing2 = create_listing(
        db_session,
        title="Other Item",
        description="Description",
        price=20.0,
        image_urls=[],
        user_id=other_user.id,
        condition="Good",
        category="Books",
        contact_email="buyer1@charlotte.edu"
    )
    
    # Check that profile user only sees own listings
    profile_listings = db_session.query(Listing).filter(Listing.user_id == profile_user.id).all()
    assert len(profile_listings) == 1
    assert profile_listings[0].title == "Profile Item"
    
    # Check that other user only sees own listings
    other_listings = db_session.query(Listing).filter(Listing.user_id == other_user.id).all()
    assert len(other_listings) == 1
    assert other_listings[0].title == "Other Item"

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
