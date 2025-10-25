from sqlalchemy import Column, Integer, String, Float, Text, DateTime,ForeignKey, func
from sqlalchemy.orm import relationship
from app.db import Base

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

      # Foreign key to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="listings")

    # One-to-many relationship to images
    images = relationship("Image", back_populates="listing", cascade="all, delete-orphan")