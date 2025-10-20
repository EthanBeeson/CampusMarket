from app.db import SessionLocal, Base, engine
from app.crud.listings import create_listing
from app.models.listing import Listing  # Needed for duplicate check

def seed_database():
    """Populate the database with initial demo data if empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Only seed if no listings exist
        if db.query(Listing).count() == 0:
            create_listing(
                db,
                title="Laptop",
                description="Laptop is in great condition, barely used.",
                price=700.00,
                image_urls=["app/images/laptop1.jpg"]
            )
        else:
            print("Database already contains listings, skipping seeding.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()