"""
Create a shared demo database with mock users and listings.

Outputs: campus_market_global.db in the project root.

Usage:
    python scripts/seed_global_db.py

You can override the output path with the GLOBAL_DB_PATH env var.
"""
import os
import re
import sys
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PIL import Image as PILImage, ImageDraw

# Ensure app package is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage import get_upload_subdir
from app.db import Base
from app.models.user import User
from app.models.listing import Listing
from app.models.image import Image
from app.crud.users import hash_password


DB_PATH = os.getenv("GLOBAL_DB_PATH", "campus_market_global.db")
DB_URL = f"sqlite:///{DB_PATH}"
DEMO_IMAGE_DIR = Path(get_upload_subdir("demo"))
DEMO_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
MACBOOK_SRC = Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/pexels-morningtrain-18105.jpg")
TEXTBOOK_SRCS = [
    Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/textbooks.jpg"),
    Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/College-Textbooks.jpg"),
]
TI84_SRC = Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/Calc.jpg")
DORM_FRIDGE_SRCS = [
    Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/mini-fridge-hub-page-hero-e15cfba.jpg"),
    Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/FHMA24_Insignia-Mini-Fridge-with-Top-Freezer_Andrea-Landowski_01_STedit.jpeg"),
]
XBOX_SRCS = [
    Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/xbox.jpg"),
    Path("/Users/anirudhpentakota/Desktop/Senior Design/CampusMarket/app/images/xbox 2.jpg"),
]


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "listing"


def create_placeholder_image(path: Path, title: str, price: float):
    """Generate a simple placeholder image with the listing title/price."""
    width, height = 900, 600
    bg_color = (245, 248, 250)
    text_color = (0, 80, 53)
    sub_color = (80, 80, 80)

    img = PILImage.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    title_text = title[:32] + ("…" if len(title) > 32 else "")
    price_text = f"${price:,.0f}"

    draw.text((40, 260), title_text, fill=text_color)
    draw.text((40, 320), price_text, fill=sub_color)

    img.save(path)


def seed():
    # fresh file each run
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            print(f"Cannot remove '{DB_PATH}' because it is open in another process.")
            print("Please stop any running Streamlit app instances, database viewers, or other processes that may be using the file, then retry.")
            print("If you want the script to continue without deleting the existing DB, set the GLOBAL_DB_PATH environment variable to a different filename and re-run.")
            sys.exit(1)

    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # --- Users ---
        users = [
            User(
                email="mia.harris@charlotte.edu",
                hashed_password=hash_password("Market!123"),
                full_name="Mia Harris",
                display_name="MiaH",
                phone="704-555-1122",
                bio="Love finding good deals on campus.",
            ),
            User(
                email="devon.james@charlotte.edu",
                hashed_password=hash_password("SellIt!234"),
                full_name="Devon James",
                display_name="DevonJ",
                phone="704-555-2233",
                bio="Electronics enthusiast and part-time tutor.",
            ),
            User(
                email="lena.cho@charlotte.edu",
                hashed_password=hash_password("StudyHub!345"),
                full_name="Lena Cho",
                display_name="LenaC",
                phone="704-555-3344",
                bio="CS student. Always coding, often selling gadgets.",
            ),
        ]
        db.add_all(users)
        db.commit()
        for u in users:
            db.refresh(u)

        # Helper to map emails to ids
        user_by_email = {u.email: u.id for u in users}

        # --- Listings ---
        listings = [
            dict(
                title="MacBook Air M1",
                description="13-inch, 8GB RAM, 256GB SSD. Great condition, used for one semester.",
                price=750.00,
                condition="Like New",
                category="Electronics",
                user_email="mia.harris@charlotte.edu",
                contact_email="mia.harris@charlotte.edu",
                contact_phone="704-555-1122",
                image_sources=[MACBOOK_SRC],
            ),
            dict(
                title="TI-84 Plus CE Calculator",
                description="Perfect for calculus. Includes charger and case.",
                price=90.00,
                condition="Good",
                category="Electronics",
                user_email="devon.james@charlotte.edu",
                contact_email="devon.james@charlotte.edu",
                contact_phone="704-555-2233",
                image_sources=[TI84_SRC],
            ),
            dict(
                title="Dorm Mini Fridge",
                description="3.2 cu ft, clean and works well. Pickup only.",
                price=120.00,
                condition="Good",
                category="Furniture",
                user_email="lena.cho@charlotte.edu",
                contact_email="lena.cho@charlotte.edu",
                contact_phone="704-555-3344",
                image_sources=DORM_FRIDGE_SRCS,
            ),
            dict(
                title="Data Structures Textbook",
                description="Used, light notes inside. ISBN: 978-0134854195.",
                price=35.00,
                condition="Fair",
                category="Books",
                user_email="mia.harris@charlotte.edu",
                contact_email="mia.harris@charlotte.edu",
                contact_phone="mia.harris@charlotte.edu",
                image_sources=TEXTBOOK_SRCS,
            ),
            dict(
                title="Xbox Series S",
                description="Comes with one controller. Hardly used.",
                price=210.00,
                condition="Like New",
                category="Electronics",
                user_email="devon.james@charlotte.edu",
                contact_email="devon.james@charlotte.edu",
                contact_phone="704-555-2233",
                image_sources=XBOX_SRCS,
            ),
        ]

        for data in listings:
            target_paths = []
            image_sources = data.get("image_sources") or []

            # Copy provided sources when available
            for idx, src in enumerate(image_sources):
                if isinstance(src, Path) and src.exists():
                    suffix = src.suffix if src.suffix else ".jpg"
                    dest = DEMO_IMAGE_DIR / f"{slugify(data['title'])}_{idx}{suffix}"
                    shutil.copyfile(src, dest)
                    target_paths.append(dest)

            # Fallback: generate a placeholder if nothing was copied
            if not target_paths:
                dest = DEMO_IMAGE_DIR / f"{slugify(data['title'])}.png"
                create_placeholder_image(dest, data["title"], data["price"])
                target_paths.append(dest)

            listing = Listing(
                title=data["title"],
                description=data["description"],
                price=data["price"],
                condition=data["condition"],
                category=data["category"],
                user_id=user_by_email[data["user_email"]],
                contact_email=data["contact_email"],
                contact_phone=data["contact_phone"],
            )
            db.add(listing)
            db.flush()  # get listing.id
            for img_path in target_paths:
                db.add(Image(url=str(img_path), listing_id=listing.id))

        db.commit()
        print(f"Seeded demo data into {DB_PATH}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
