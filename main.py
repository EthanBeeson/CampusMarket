import streamlit as st
from app.db import Base, engine, SessionLocal
from app.models.listing import Listing
from app.models.image import Image
from app.crud.listings import create_listing, get_listings, delete_listing, search_listings


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

# Start session
db = SessionLocal()

# --- Sidebar search controls ---
st.sidebar.header("Search & Filters")
search_query = st.sidebar.text_input("Search by keyword")
min_price = st.sidebar.number_input("Min Price", min_value=0.0, step=10.0)
max_price = st.sidebar.number_input("Max Price", min_value=0.0, step=10.0)

# --- Fetch filtered listings or all listings ---
if search_query or min_price or max_price:
    listings = listings = search_listings(
        db,
        keyword=search_query if search_query else None,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price > 0 else None
    )
else:
    listings = get_listings(db)

# --- Display listings returned in terminal ---
for l in listings:
    print(f"ID: {l.id}, Listing: {l.title}, Price: ${l.price}, Images: {[img.url for img in l.images]}")

# --- Display listings on homepage ---
for l in listings:
    st.subheader(f"{l.title} - ${l.price:.2f}")
    st.write(l.description)

    # Delete button
    if st.button(f"Delete Listing {l.id}", key=f"delete-{l.id}"):
        deleted = delete_listing(db, listing_id=l.id)
        if deleted:
            st.success(f"Deleted listing {l.id}")
        else:
            st.error(f"Listing {l.id} not found")
        st.rerun()

    # Show images if any
    if l.images:
        cols = st.columns(len(l.images))
        for col, img in zip(cols, l.images):
            try:
                col.image(img.url, width=150)
            except FileNotFoundError:
                col.text("[Image not found]")
    st.markdown("---")

db.close()

