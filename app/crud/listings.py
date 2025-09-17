from sqlalchemy.orm import Session
from app.models.listing import Listing
from app.models.image import Image

#====== CRUD Operations for Listings ======#
# These CRUD functions are to be use in main.py and future API endpoints
# for creating, reading, and deleting listings along with their images.
#=========================================#

# Create a listing
def create_listing(db: Session, title: str, description: str, price: float, image_urls: list):
    listing = Listing(title=title, description=description, price=price)
    
    # Attach images
    images = [Image(url=url) for url in image_urls]
    # Connects all images to the listing by the SQLAlchemy listing.images list
    listing.images.extend(images)
    
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

# Query all listings
def get_listings(db: Session):
    return db.query(Listing).all()

# Get a listing by ID
def get_listing(db: Session, listing_id: int):
    return db.query(Listing).filter(Listing.id == listing_id).first()

# Delete a listing
def delete_listing(db: Session, listing_id: int):
    listing = get_listing(db, listing_id)
    if listing:
        db.delete(listing)
        db.commit()
        return True
    return False

# Update a listing
def update_listing(db: Session, listing_id: int, title: str = None, description: str = None,
                   price: float = None, add_images: list = None, remove_image_ids: list = None):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return None

    # Update fields if provided
    if title is not None:
        listing.title = title
    if description is not None:
        listing.description = description
    if price is not None:
        listing.price = price

    # Add new images
    if add_images:
        new_images = [Image(url=url) for url in add_images]
        listing.images.extend(new_images)

    # Remove specific images by ID
    if remove_image_ids:
        for img in listing.images[:]:  # iterate over a copy to avoid modification errors
            if img.id in remove_image_ids:
                listing.images.remove(img)
                db.delete(img)

    db.commit()
    db.refresh(listing)
    return listing
#=========================================#