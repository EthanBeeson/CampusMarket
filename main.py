from app.db import Base, engine, SessionLocal
from app.models.listing import Listing
from app.models.image import Image
from app.crud.listings import create_listing, get_listings, delete_listing

# Create database tables
Base.metadata.create_all(bind=engine)

#======== Example Usage ========#
# Testing CRUD functions with local variables
# ==============================#

# Start session
db = SessionLocal()

# Create a listing with images
listing = create_listing(
    db,
    title="Used Laptop",
    description="Selling my old laptop, works perfectly.",
    price=350.00,
    image_urls=["laptop1.jpg", "laptop2.jpg"]
)
print(f"Created listing: {listing.title} with {len(listing.images)} images")

# Query all listings
all_listings = get_listings(db)
for l in all_listings:
    print(f"ID: {l.id}, Listing: {l.title}, Price: ${l.price}, Images: {[img.url for img in l.images]}")

'''
# Update listing: change title, price, add and remove images
updated_listing = update_listing(
    db,
    listing_id=listing.id,
    title="CS Textbook - Updated",
    price=25.0,
    add_images=["textbook3.jpg"],
    remove_image_ids=[listing.images[0].id]  # remove first image
)

print(f"\nUpdated listing: {updated_listing.title}, Price: ${updated_listing.price}")
print("Images after update:", [img.url for img in updated_listing.images])
'''

# Delete the listing
deleted = delete_listing(db, listing.id)
print(f"Deleted listing: {deleted}")

db.close()

