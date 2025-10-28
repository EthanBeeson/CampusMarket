from sqlalchemy.orm import Session
from app.models.listing import Listing
from app.models.image import Image
from sqlalchemy import or_
from rapidfuzz import fuzz

# Allowed values for the listing condition. Keep in sync with UI options.
ALLOWED_CONDITIONS = ["New", "Like New", "Good", "Fair", "For Parts"]


#====== CRUD Operations for Listings ======#
# These CRUD functions are to be use in main.py and future API endpoints
# for creating, reading, and deleting listings along with their images.
#=========================================#

# Create a listing
def create_listing(db: Session, title: str, description: str, price: float, image_urls: list, user_id: int, condition: str = "Good", contact_email: str = None,
contact_phone: str = None):
    """Create a listing and persist images, user and condition."""
    # Validate condition
    if condition is None:
        condition = "Good"
    if not isinstance(condition, str):
        raise ValueError("Condition must be a string")
    condition_clean = condition.strip()
    if condition_clean not in ALLOWED_CONDITIONS:
        raise ValueError(f"Invalid condition '{condition}'. Allowed: {ALLOWED_CONDITIONS}")

    listing = Listing(title=title, description=description, price=price, user_id=user_id, condition=condition_clean)
    
    # Attach images
    images = [Image(url=url) for url in image_urls]
    # Connects all images to the listing by the SQLAlchemy listing.images list
    listing.images.extend(images)

    if price < 0:
        raise ValueError("Price cannot be negative")
    
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
                   price: float = None, condition: str = None, add_images: list = None, remove_image_ids: list = None):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return None

    # Update fields if provided
    if title is not None:
        listing.title = title
    if description is not None:
        listing.description = description
    if price is not None:
        try:
            price_val = float(price)
        except (TypeError, ValueError):
            raise ValueError("Price must be a number")
        if price_val < 0:
            raise ValueError("Price must be non-negative")
        listing.price = price_val
    

    # Update condition if provided
    if condition is not None:
        if not isinstance(condition, str):
            raise ValueError("Condition must be a string")
        condition_clean = condition.strip()
        if condition_clean not in ALLOWED_CONDITIONS:
            raise ValueError(f"Invalid condition '{condition}'. Allowed: {ALLOWED_CONDITIONS}")
        listing.condition = condition_clean
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


# ====== Search Listings Functionality ======#
# This function allows searching listings by keywords in title or description,
# as well as filtering by price range. It supports both exact and fuzzy matches.
#============================================#

def search_listings(db, keyword: str = None, threshold: int = 60,
                    min_price: float = None, max_price: float = None,
                    conditions: list = None):
    # --- Start with all listings ---
    q = db.query(Listing)

    # --- Apply price filters early ---
    if min_price is not None:
        q = q.filter(Listing.price >= min_price)
    if max_price is not None:
        q = q.filter(Listing.price <= max_price)
    # --- Apply condition filters if provided ---
    if conditions:
        # ensure we have a list of values
        if isinstance(conditions, (list, tuple, set)) and len(conditions) > 0:
            q = q.filter(Listing.condition.in_(list(conditions)))
    listings = q.all()

    # --- Apply fuzzy keyword search if keyword is provided ---
    if keyword and keyword.strip():
        keyword_norm = keyword.lower().strip()
        results = []
        for listing in listings:
            title_norm = listing.title.lower().strip()
            desc_norm = listing.description.lower().strip()
            title_score = fuzz.token_sort_ratio(keyword_norm, title_norm)
            desc_score = fuzz.token_sort_ratio(keyword_norm, desc_norm)
            if max(title_score, desc_score) >= threshold:
                results.append(listing)
        return results

    # --- If no keyword provided, just return filtered results ---
    return listings


# ====== Mark Item As Sold Functionality ======#
# This function allows users to mark their items
#as sold
#============================================#
class ForbiddenAction(Exception):
    pass

def get_listing_by_id(db: Session, listing_id: int):
    return db.get(Listing, listing_id)


def ensure_owner(listing: Listing | None, user_id: int):
    if listing is None:
        raise ValueError("Listing not found")
    if listing.user_id != user_id:
        raise ForbiddenAction("You do not own this listing")
    

def mark_listing_sold(db: Session, listing_id: int, user_id: int) -> Listing:
    listing = db.query(Listing).filter_by(id=listing_id).first()
    if not listing:
        return False
    if listing.user_id != user_id:
        raise ForbiddenAction("You do not own this listing")
    listing.is_sold = True
    db.commit()
    return True