# app/pages/4_Profile.py
import streamlit as st
import os
import re
from PIL import Image as PILImage
import io
import base64

# SQLAlchemy imports
from app.db import SessionLocal
from sqlalchemy import select
from app.models.listing import Listing
from app.models.image import Image
from app.models.user import User

# Charlotte colors styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #005035;  /* dark green */
    }
    .profile-container {
        background-color: #87B481;  /* light green */
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .listings-container {
        background-color: #87B481;  /* light green */
        padding: 20px;
        border-radius: 10px;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: white;
        color: black;
    }
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
    }
    .listing-card {
        background-color: #E8F5E8;  /* Light green background */
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 6px solid #005035;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .listing-title {
        color: #005035;  /* Dark green */
        font-size: 1.4em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .listing-price {
        color: #2E7D32;  /* Medium green */
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .listing-description {
        color: #333333;  /* Dark gray for readability */
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .listing-date {
        color: #666666;  /* Medium gray */
        font-size: 0.9em;
        font-style: italic;
    }
    .delete-btn {
        background-color: #ff4444 !important;
        color: white !important;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
    }
    .logout-btn {
        background-color: #ff4444 !important;
        color: white !important;
    }
    .no-listings {
        text-align: center;
        padding: 30px;
        color: #005035;
        font-size: 1.1em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def init_db_session():
    """Initialize database session"""
    return SessionLocal()

def get_user_listings(db, user_id):
    """Get all listings for the current user"""
    stmt = select(Listing).where(Listing.user_id == user_id)
    return db.execute(stmt).scalars().all()

def get_listing_images(db, listing_id):
    """Get all images for a listing"""
    stmt = select(Image).where(Image.listing_id == listing_id)
    return db.execute(stmt).scalars().all()

def save_profile_picture(uploaded_file, user_id):
    """Save profile picture to uploads directory"""
    upload_dir = "uploads/profile_pictures"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create filename with user_id
    file_extension = os.path.splitext(uploaded_file.name)[1]
    filename = f"profile_{user_id}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def load_profile_picture(user_id):
    """Load profile picture if exists"""
    upload_dir = "uploads/profile_pictures"
    possible_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    
    for ext in possible_extensions:
        file_path = os.path.join(upload_dir, f"profile_{user_id}{ext}")
        if os.path.exists(file_path):
            return file_path
    return None

def delete_listing_safe(listing_id, current_user_id):
    """Safely delete a listing with ownership verification"""
    db = SessionLocal()
    try:
        # Get the listing with a fresh query
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        
        if not listing:
            st.error("❌ Listing not found.")
            return False
            
        # Verify ownership - this is the crucial check
        if listing.user_id != current_user_id:
            st.error("🚫 You are not authorized to delete this listing.")
            return False
        
        # Get associated images
        images = db.query(Image).filter(Image.listing_id == listing_id).all()
        
        # Delete associated images
        for img in images:
            if os.path.exists(img.url):
                try:
                    os.remove(img.url)
                    st.info(f"🗑️ Deleted image: {os.path.basename(img.url)}")
                except OSError as e:
                    st.warning(f"⚠️ Could not delete image file: {e}")
            db.delete(img)
        
        # Delete the listing
        db.delete(listing)
        db.commit()
        st.success("✅ Listing deleted successfully!")
        return True
        
    except Exception as e:
        db.rollback()
        st.error(f"❌ Error deleting listing: {str(e)}")
        return False
    finally:
        db.close()

def display_listing_card(listing, images, current_user_id):
    """Display a listing card with ownership-based delete button"""
    st.markdown(f"""
    <div class="listing-card">
        <div class="listing-title">{listing.title}</div>
        <div class="listing-price">${listing.price:.2f}</div>
        <div class="listing-description">{listing.description}</div>
        <div class="listing-date">Posted on {listing.created_at.strftime('%B %d, %Y at %I:%M %p')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Debug info - show ownership status
    st.write(f"🔍 **Debug Info:** Listing User ID: {listing.user_id}, Current User ID: {current_user_id}, Can Delete: {listing.user_id == current_user_id}")
    
    # Display listing images
    if images:
        st.write("**Images:**")
        image_cols = st.columns(min(3, len(images)))
        for idx, img in enumerate(images):
            if idx < 3:  # Show max 3 images
                with image_cols[idx]:
                    if os.path.exists(img.url):
                        st.image(img.url, use_column_width=True, caption=f"Image {idx+1}")
    
    # Only show delete button if user owns the listing
    if listing.user_id == current_user_id:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Delete My Listing", key=f"delete_{listing.id}", use_container_width=True):
                if delete_listing_safe(listing.id, current_user_id):
                    st.rerun()
    else:
        st.warning("🔒 This listing belongs to another user")
    
    st.markdown("---")

# Main Profile Page
st.set_page_config(page_title="Profile - Campus Market", layout="wide")

st.title("👤 Your Profile")

# Check if user is logged in
if "user_id" not in st.session_state or "user_email" not in st.session_state:
    st.error("Please log in to view your profile.")
    st.stop()

user_id = st.session_state["user_id"]
user_email = st.session_state["user_email"]

# Profile Section
st.markdown('<div class="profile-container">', unsafe_allow_html=True)
st.header("Profile Information")

# Display user email (username)
st.write(f"**Email:** {user_email}")
st.write(f"**User ID:** {user_id}")

# Profile Picture Section
st.subheader("Profile Picture")

# Load existing profile picture
profile_pic_path = load_profile_picture(user_id)

# Display current profile picture
col1, col2 = st.columns([1, 2])
with col1:
    if profile_pic_path:
        st.image(profile_pic_path, width=150, caption="Current Profile Picture")
    else:
        st.info("No profile picture uploaded yet.")

with col2:
    # Upload new profile picture
    uploaded_file = st.file_uploader(
        "Upload a new profile picture", 
        type=['jpg', 'jpeg', 'png'],
        key="profile_pic_uploader"
    )
    
    if uploaded_file is not None:
        # Validate file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            st.error("File size too large. Please upload an image smaller than 5MB.")
        else:
            try:
                # Save the new profile picture
                new_profile_path = save_profile_picture(uploaded_file, user_id)
                
                # Remove old profile pictures
                upload_dir = "uploads/profile_pictures"
                for file in os.listdir(upload_dir):
                    if file.startswith(f"profile_{user_id}") and file != os.path.basename(new_profile_path):
                        os.remove(os.path.join(upload_dir, file))
                
                st.success("Profile picture updated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error uploading profile picture: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# User's Listings Section
st.markdown('<div class="listings-container">', unsafe_allow_html=True)
st.header("📋 Your Listings")

db = SessionLocal()
try:
    user_listings = get_user_listings(db, user_id)
    
    if not user_listings:
        st.markdown('<div class="no-listings">', unsafe_allow_html=True)
        st.write("You haven't created any listings yet.")
        st.page_link("pages/1_create_listing.py", label="Create Your First Listing", icon="📝")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write(f"**Total Listings:** {len(user_listings)}")
        
        # Display each listing - pass current_user_id for authorization
        for listing in user_listings:
            listing_images = get_listing_images(db, listing.id)
            display_listing_card(listing, listing_images, user_id)
            
finally:
    db.close()

st.markdown('</div>', unsafe_allow_html=True)

# Enhanced Quick Actions Section with Logout
st.markdown("---")
st.header("Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝 Create New Listing", use_container_width=True):
        st.switch_page("pages/1_create_listing.py")

with col2:
    if st.button("🔍 Browse Listings", use_container_width=True):
        st.switch_page("main.py")

with col3:
    # Enhanced Logout button with confirmation
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logged out successfully!")
        st.rerun()