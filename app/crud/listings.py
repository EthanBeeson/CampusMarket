from sqlalchemy.orm import Session
from app.models.listing import Listing
from app.models.image import Image
from sqlalchemy import or_
from rapidfuzz import fuzz

# Allowed values for the listing condition. Keep in sync with UI options.
ALLOWED_CONDITIONS = ["New", "Like New", "Good", "Fair", "For Parts"]
# Allowed categories for listings
ALLOWED_CATEGORIES = ["Books", "Electronics", "Furniture", "Clothing", "Hobby", "Other"]


#====== CRUD Operations for Listings ======#
# These CRUD functions are used in home.py and future API endpoints
# for creating, reading, and deleting listings along with their images.
#=========================================#

# Create a listing
def create_listing(db: Session, title, description=None, price: float = None, image_urls: list | None = None,
                   user_id: int | None = None, condition: str = "Good", contact_email: str = None,
                   contact_phone: str = None, category: str = "Other"):
    """
    Create a listing and persist images, user and condition.

    Supports two call styles:
    - Keyword/standard: create_listing(db, title="T", description="D", price=1.0, image_urls=[], user_id=1, ...)
    - Legacy positional: create_listing(db, user_id, title, description, price, condition, category)
    """
    # Default images list
    if image_urls is None:
        image_urls = []

    # Detect legacy positional ordering where user_id is the second arg and condition/category shifted
    if isinstance(title, int) and isinstance(user_id, str) and user_id in ALLOWED_CONDITIONS:
        legacy_user_id = title
        legacy_title = description
        legacy_description = price
        legacy_price = image_urls
        legacy_condition = user_id
        legacy_category = condition if isinstance(condition, str) else "Other"

        # Remap into expected fields
        title = legacy_title
        description = legacy_description
        try:
            price = float(legacy_price)
        except (TypeError, ValueError):
            raise ValueError("Price must be a number")
        user_id = legacy_user_id
        condition = legacy_condition
        category = legacy_category
        image_urls = []

    # Validate presence of required fields
    if user_id is None:
        raise ValueError("user_id is required")
    if title is None or description is None or price is None:
        raise ValueError("title, description, and price are required")

    # Validate and normalize price
    try:
        price_val = float(price)
    except (TypeError, ValueError):
        raise ValueError("Price must be a number")
    if price_val < 0:
        raise ValueError("Price cannot be negative")

    # Validate condition
    if condition is None:
        condition = "Good"
    if not isinstance(condition, str):
        raise ValueError("Condition must be a string")
    condition_clean = condition.strip()
    if condition_clean not in ALLOWED_CONDITIONS:
        raise ValueError(f"Invalid condition '{condition}'. Allowed: {ALLOWED_CONDITIONS}")

    # Validate and set category
    if category is None:
        category = "Other"
    if not isinstance(category, str):
        raise ValueError("Category must be a string")
    category_clean = category.strip()
    if category_clean not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Allowed: {ALLOWED_CATEGORIES}")

    listing = Listing(
        title=title,
        description=description,
        price=price_val,
        user_id=user_id,
        condition=condition_clean,
        category=category_clean,
        contact_email=contact_email,
        contact_phone=contact_phone,
    )

    # Attach images
    images = [Image(url=url) for url in image_urls]
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
                   price: float = None, condition: str = None, category: str = None, add_images: list = None, remove_image_ids: list = None):
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
    # Update category if provided
    if category is not None:
        if not isinstance(category, str):
            raise ValueError("Category must be a string")
        category_clean = category.strip()
        if category_clean not in ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Allowed: {ALLOWED_CATEGORIES}")
        listing.category = category_clean
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
                    conditions: list = None, categories: list = None):
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
    # --- Apply category filters if provided ---
    if categories:
        if isinstance(categories, (list, tuple, set)) and len(categories) > 0:
            q = q.filter(Listing.category.in_(list(categories)))
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
