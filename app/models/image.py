from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"))

    # Back-reference to listing
    listing = relationship("Listing", back_populates="images")
