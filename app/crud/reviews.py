from sqlalchemy.orm import Session
from app.models.review import Review
from app.models.listing import Listing
from sqlalchemy import func as sqlfunc

# Create a review
def create_review(db: Session, reviewer_id: int, reviewed_user_id: int, rating: float, 
                  comment: str = None, listing_id: int = None):
    """Create a review for a user."""
    if rating < 1.0 or rating > 5.0:
        raise ValueError("Rating must be between 1.0 and 5.0")
    if not isinstance(rating, (int, float)):
        raise ValueError("Rating must be a number")
    if reviewer_id == reviewed_user_id:
        raise ValueError("You cannot review yourself")
    
    review = Review(
        reviewer_id=reviewer_id,
        reviewed_user_id=reviewed_user_id,
        rating=rating,
        comment=comment,
        listing_id=listing_id
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

# Get all reviews for a user (reviews received)
def get_reviews_for_user(db: Session, user_id: int):
    """Get all reviews received by a user, ordered by most recent."""
    return db.query(Review).filter(Review.reviewed_user_id == user_id).order_by(Review.created_at.desc()).all()

# Get average rating for a user
def get_user_average_rating(db: Session, user_id: int):
    """Get average rating for a user; returns None if no reviews."""
    result = db.query(sqlfunc.avg(Review.rating)).filter(Review.reviewed_user_id == user_id).scalar()
    return result

# Delete a review
def delete_review(db: Session, review_id: int):
    """Delete a review by ID."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        db.delete(review)
        db.commit()
        return True
    return False

# Get a single review
def get_review(db: Session, review_id: int):
    """Get a review by ID."""
    return db.query(Review).filter(Review.id == review_id).first()

# Check if a user has already reviewed another user
def has_user_reviewed(db: Session, reviewer_id: int, reviewed_user_id: int):
    """Check if reviewer has already left a review for reviewed_user."""
    existing = db.query(Review).filter(
        Review.reviewer_id == reviewer_id,
        Review.reviewed_user_id == reviewed_user_id
    ).first()
    return existing is not None

# Update a review
def update_review(db: Session, review_id: int, rating: float = None, comment: str = None):
    """Update an existing review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return None
    
    if rating is not None:
        if rating < 1.0 or rating > 5.0:
            raise ValueError("Rating must be between 1.0 and 5.0")
        review.rating = rating
    
    if comment is not None:
        review.comment = comment
    
    db.commit()
    db.refresh(review)
    return review
