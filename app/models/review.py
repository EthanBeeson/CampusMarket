from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    # Reviewer (the user leaving the review)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Reviewee (the user being reviewed / owner)
    reviewed_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # The listing related to this review (optional)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=True)
    
    # Review content
    rating = Column(Float, nullable=False)  # 1.0 to 5.0
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="reviews_given")
    reviewed_user = relationship("User", foreign_keys=[reviewed_user_id], backref="reviews_received")
    listing = relationship("Listing", backref="reviews")
