import streamlit as st
from app.db import Base, engine, SessionLocal
from app.models.listing import Listing
from app.models.image import Image
from app.crud.listings import create_listing, get_listings, delete_listing, search_listings

# Create database tables
Base.metadata.create_all(bind=engine)

#=============== Streamlit Base Homepage ==================#

# Green background for Charlotte theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #005035; /* UNCC green */
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
    listings = search_listings(
        db,
        keyword=search_query if search_query else None,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price > 0 else None
    )
else:
    listings = get_listings(db)

# --- Display "No Listings" message if empty ---
if not listings:
    st.markdown(
        """
        <div style="
            background-color:#004830;
            color:#ffffff;
            padding:20px;
            border-radius:12px;
            text-align:center;
            font-size:18px;
            margin-top:20px;
            ">
            <b>No listings found</b><br>
            Try adjusting your search or filters — or check back later for new items!
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # --- Display listings ---
    for l in listings:
        st.subheader(f"{l.title} - ${l.price:.2f}")
        # Show condition if available (fallback to 'Unknown' for older rows)
        condition = getattr(l, "condition", "Unknown")
        st.markdown(f"**Condition:** {condition}")
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
