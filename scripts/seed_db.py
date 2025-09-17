from app.db import SessionLocal, Base, engine
from app.crud.listings import create_listing

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# This script is used to add mock data to the database for testing purposes
create_listing(
    db,
    title="Used Laptop",
    description="Selling my old laptop",
    price=350.00,
    image_urls=["app/images/laptop1.jpg", "app/images/laptop2.jpg"]
)

db.close()
