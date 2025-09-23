import streamlit as st
from app.db import Base, engine, SessionLocal
from app.models.listing import Listing
from app.models.image import Image
from app.crud.listings import create_listing, get_listings, delete_listing

# Create database tables
Base.metadata.create_all(bind=engine)

#=============== Streamlit Base Homepage ==================

# Green backgorund for charlotte
st.markdown(
    """
    <style>
    .stApp {
        background-color: #005035; /* uncc green */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("🏫 Campus Market")
st.write("Welcome to Campus Market! Buy and sell items with UNCC students.")

# Sidebar for adding search/filter later
st.sidebar.header("Filters (coming soon)")
st.sidebar.text("Filter by keyword, price, category...")

# Start session
db = SessionLocal()

# Query all listings
all_listings = get_listings(db)
for l in all_listings:
    print(f"ID: {l.id}, Listing: {l.title}, Price: ${l.price}, Images: {[img.url for img in l.images]}")

# Streamlit Display Listings
if all_listings:
    for l in all_listings:
        st.subheader(f"{l.title} - ${l.price:.2f}")
        st.write(l.description)

        # Show images if any
        if l.images:
            cols = st.columns(len(l.images))
            for col, img in zip(cols, l.images):
                try:
                    col.image(img.url, width=150)
                except FileNotFoundError:
                    col.text("[Image not found]")
        st.markdown("---")
else:
    st.info("No listings available yet.")

db.close()

