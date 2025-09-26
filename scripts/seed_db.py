from app.db import SessionLocal, Base, engine
from app.crud.listings import create_listing

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# This script is used to add mock data to the database for testing purposes
create_listing(
    db,
    title="Bike",
    description="This bike is in great condition, barely used.",
    price=700.00,
    image_urls=["app/images/laptop1.jpg"]
)

db.close()
