# tests/test_reviews.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.crud.reviews import (
    create_review,
    get_reviews_for_user,
    get_user_average_rating,
    delete_review,
    get_review,
    has_user_reviewed,
    update_review
)
from app.crud.users import create_user
from app.models.review import Review
from app.models.user import User
from app.models.listing import Listing
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
def test_users(db_session):
    """Create test users for review tests"""
    user1 = create_user(db_session, "reviewer@charlotte.edu", "Password123!")
    user2 = create_user(db_session, "reviewee@charlotte.edu", "Password123!")
    user3 = create_user(db_session, "reviewer2@charlotte.edu", "Password123!")
    return {"reviewer": user1, "reviewee": user2, "reviewer2": user3}

# ----------------- Create Review Tests -----------------
def test_create_review_success(db_session, test_users):
    """Test successful review creation"""
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=4.5,
        comment="Great seller!"
    )
    
    assert review.id is not None
    assert review.reviewer_id == test_users["reviewer"].id
    assert review.reviewed_user_id == test_users["reviewee"].id
    assert review.rating == 4.5
    assert review.comment == "Great seller!"

def test_create_review_without_comment(db_session, test_users):
    """Test review creation without comment"""
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=3.0
    )
    
    assert review.comment is None
    assert review.rating == 3.0

def test_create_review_with_listing(db_session, test_users):
    """Test review creation with listing reference"""
    # Create a listing for reference
    listing = Listing(
        title="Test Item",
        description="Test description",
        price=10.0,
        condition="Good",
        category="Other",
        user_id=test_users["reviewer"].id
    )
    db_session.add(listing)
    db_session.commit()
    
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=5.0,
        comment="Perfect transaction",
        listing_id=listing.id
    )
    
    assert review.listing_id == listing.id

def test_create_review_invalid_rating_too_high(db_session, test_users):
    """Test review creation rejects rating > 5.0"""
    with pytest.raises(ValueError, match="between 1.0 and 5.0"):
        create_review(
            db_session,
            reviewer_id=test_users["reviewer"].id,
            reviewed_user_id=test_users["reviewee"].id,
            rating=5.5
        )

def test_create_review_prevents_self_review(db_session, test_users):
    """Test that users cannot review themselves"""
    with pytest.raises(ValueError, match="cannot review yourself"):
        create_review(
            db_session,
            reviewer_id=test_users["reviewer"].id,
            reviewed_user_id=test_users["reviewer"].id,
            rating=3.0
        )

# ----------------- Get Reviews Tests -----------------
def test_get_reviews_for_user(db_session, test_users):
    """Test retrieving all reviews for a user"""
    # Create multiple reviews for same user
    create_review(db_session, test_users["reviewer"].id, test_users["reviewee"].id, 5.0, "Excellent!")
    create_review(db_session, test_users["reviewer2"].id, test_users["reviewee"].id, 4.0, "Good seller")
    
    reviews = get_reviews_for_user(db_session, test_users["reviewee"].id)
    
    assert len(reviews) == 2
    assert all(r.reviewed_user_id == test_users["reviewee"].id for r in reviews)

def test_get_reviews_for_user_no_reviews(db_session, test_users):
    """Test retrieving reviews for user with no reviews"""
    reviews = get_reviews_for_user(db_session, test_users["reviewee"].id)
    
    assert len(reviews) == 0


def test_get_review_by_id(db_session, test_users):
    """Test retrieving a specific review by ID"""
    created_review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=4.5
    )
    
    retrieved_review = get_review(db_session, created_review.id)
    
    assert retrieved_review is not None
    assert retrieved_review.id == created_review.id
    assert retrieved_review.rating == 4.5

def test_get_review_not_found(db_session):
    """Test retrieving non-existent review returns None"""
    review = get_review(db_session, 999)
    
    assert review is None

# ----------------- Average Rating Tests -----------------
def test_get_user_average_rating(db_session, test_users):
    """Test calculating average rating for a user"""
    create_review(db_session, test_users["reviewer"].id, test_users["reviewee"].id, 5.0)
    create_review(db_session, test_users["reviewer2"].id, test_users["reviewee"].id, 3.0)
    
    avg_rating = get_user_average_rating(db_session, test_users["reviewee"].id)
    
    assert avg_rating == 4.0

def test_get_user_average_rating_no_reviews(db_session, test_users):
    """Test average rating for user with no reviews"""
    avg_rating = get_user_average_rating(db_session, test_users["reviewee"].id)
    
    assert avg_rating is None

def test_get_user_average_rating_single_review(db_session, test_users):
    """Test average rating with single review"""
    create_review(db_session, test_users["reviewer"].id, test_users["reviewee"].id, 4.5)
    
    avg_rating = get_user_average_rating(db_session, test_users["reviewee"].id)
    
    assert avg_rating == 4.5

# ----------------- Delete Review Tests -----------------
def test_delete_review_success(db_session, test_users):
    """Test successful review deletion"""
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=3.0
    )
    
    success = delete_review(db_session, review.id)
    
    assert success == True
    assert get_review(db_session, review.id) is None

def test_delete_review_not_found(db_session):
    """Test deleting non-existent review"""
    success = delete_review(db_session, 999)
    
    assert success == False

# ----------------- Has User Reviewed Tests -----------------
def test_has_user_reviewed_true(db_session, test_users):
    """Test has_user_reviewed returns True when review exists"""
    create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=4.0
    )
    
    has_reviewed = has_user_reviewed(
        db_session,
        test_users["reviewer"].id,
        test_users["reviewee"].id
    )
    
    assert has_reviewed == True

def test_has_user_reviewed_false(db_session, test_users):
    """Test has_user_reviewed returns False when no review exists"""
    has_reviewed = has_user_reviewed(
        db_session,
        test_users["reviewer"].id,
        test_users["reviewee"].id
    )
    
    assert has_reviewed == False

def test_has_user_reviewed_directional(db_session, test_users):
    """Test that has_user_reviewed is directional"""
    # User1 reviews User2
    create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=4.0
    )
    
    # User2 did not review User1
    has_reviewed = has_user_reviewed(
        db_session,
        test_users["reviewee"].id,
        test_users["reviewer"].id
    )
    
    assert has_reviewed == False

# ----------------- Update Review Tests -----------------
def test_update_review_rating(db_session, test_users):
    """Test updating review rating"""
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=3.0,
        comment="Initial review"
    )
    
    updated = update_review(db_session, review.id, rating=5.0)
    
    assert updated.rating == 5.0
    assert updated.comment == "Initial review"

def test_update_review_comment(db_session, test_users):
    """Test updating review comment"""
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=4.0,
        comment="Original comment"
    )
    
    updated = update_review(db_session, review.id, comment="Updated comment")
    
    assert updated.rating == 4.0
    assert updated.comment == "Updated comment"

def test_update_review_both_fields(db_session, test_users):
    """Test updating both rating and comment"""
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=2.0,
        comment="Bad experience"
    )
    
    updated = update_review(db_session, review.id, rating=4.5, comment="Actually was better")
    
    assert updated.rating == 4.5
    assert updated.comment == "Actually was better"

def test_update_review_invalid_rating(db_session, test_users):
    """Test update rejects invalid rating"""
    review = create_review(
        db_session,
        reviewer_id=test_users["reviewer"].id,
        reviewed_user_id=test_users["reviewee"].id,
        rating=3.0
    )
    
    with pytest.raises(ValueError, match="between 1.0 and 5.0"):
        update_review(db_session, review.id, rating=6.0)

def test_update_review_not_found(db_session):
    """Test updating non-existent review"""
    result = update_review(db_session, 999, rating=3.0)
    
    assert result is None

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
