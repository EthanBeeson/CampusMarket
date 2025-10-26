from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime
from app.db import Base
from datetime import datetime

# Base class for all models
ORMBase = declarative_base()

# Example User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Optional profile fields
    full_name = Column(String(100), nullable=True)
    display_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    bio = Column(String(500), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


    # This is required for the back_populates
    listings = relationship("Listing", back_populates="user", cascade="all, delete-orphan")