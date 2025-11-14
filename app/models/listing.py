from sqlalchemy import Column, Integer, String, Float, Text, DateTime,ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from app.db import Base

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    # Condition of the item (e.g. New, Like New, Good, Fair, For Parts)
    # Provide both a client-side default and a server_default so existing
    # inserts (tests or older code) get a sensible value without migration
    condition = Column(String(20), nullable=False, default="Good", server_default="Good")
    # Category of the item (e.g. Books, Electronics). Not shown on cards by default
    # but used for filtering. Provide server_default so existing DB rows get a value.
    category = Column(String(50), nullable=False, default="Other", server_default="Other")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    #is_sold (story 15)
    is_sold = Column(Boolean, nullable=False, default=False, server_default="0")

    #contact info
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)

    # Foreign key to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="listings")

    # One-to-many relationship to images
    images = relationship("Image", back_populates="listing", cascade="all, delete-orphan")

    