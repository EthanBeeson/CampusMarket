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
from app.crud.users import update_user_profile, delete_user_profile_picture
from app.models.message import Message

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

def get_received_messages(db, user_id):
    """Get all messages received by this user"""
    return db.query(Message).filter(Message.receiver_id == user_id).order_by(Message.created_at.desc()).all()

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
        
    # Display listing images
    if images:
        st.write("**Images:**")
        image_cols = st.columns(min(3, len(images)))
        for idx, img in enumerate(images):
            if idx < 3:  # Show max 3 images
                with image_cols[idx]:
                    if os.path.exists(img.url):
                        #st.image(img.url, use_column_width=True, caption=f"Image {idx+1}")
                        st.image(img.url, use_container_width=True, caption=f"Image {idx+1}")
    
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

# Load user record for profile fields
db_user = None
db = SessionLocal()
try:
    db_user = db.query(User).filter(User.id == user_id).first()
finally:
    db.close()

# Profile info form / summary
st.subheader("Profile Details")

# Determine if profile is already populated
profile_complete = False
if db_user:
    profile_complete = any([
        bool(getattr(db_user, "full_name", "")),
        bool(getattr(db_user, "display_name", "")),
        bool(getattr(db_user, "phone", "")),
        bool(getattr(db_user, "bio", "")),
        bool(getattr(db_user, "profile_picture", "")),
    ])

# Initialize editing state: if profile is empty, start in edit/create mode
if "editing_profile" not in st.session_state:
    st.session_state["editing_profile"] = not profile_complete

if not st.session_state.get("editing_profile", False):
    # Show read-only summary with an Edit button
    st.write("**Full Name:**", getattr(db_user, "full_name", ""))
    st.write("**Display Name:**", getattr(db_user, "display_name", ""))
    st.write("**Phone:**", getattr(db_user, "phone", ""))
    st.write("**Bio:**", getattr(db_user, "bio", ""))

    col_left, col_right = st.columns([3, 1])
    with col_right:
        if st.button("Edit Profile", key=f"edit_profile_{user_id}"):
            st.session_state["editing_profile"] = True
            st.rerun()
else:
    # Editable form (prefilled)
    with st.form(key="profile_form", clear_on_submit=False):
        full_name_val = st.text_input("Full Name", value=getattr(db_user, "full_name", "") if db_user else "")
        display_name_val = st.text_input("Display Name", value=getattr(db_user, "display_name", "") if db_user else "")
        phone_val = st.text_input("Phone", value=getattr(db_user, "phone", "") if db_user else "")
        bio_val = st.text_area("Bio", value=getattr(db_user, "bio", "") if db_user else "", height=120)
        save_profile = st.form_submit_button("Save Profile")

        if save_profile:
            # Client-side validation before calling server
            errors = []
            if full_name_val and len(full_name_val.strip()) > 100:
                errors.append("Full name must be 100 characters or fewer.")
            if display_name_val and len(display_name_val.strip()) > 50:
                errors.append("Display name must be 50 characters or fewer.")
            if bio_val and len(bio_val.strip()) > 500:
                errors.append("Bio must be 500 characters or fewer.")
            # basic phone validation
            phone_pattern = r'^\+?[0-9\-\s\(\)]{7,20}$'
            if phone_val and not re.match(phone_pattern, phone_val.strip()):
                errors.append("Phone number appears invalid.")

            ## If no errors detected, proceed to update
            if errors:
                for e in errors:
                    st.error(e)
            else:
                db = SessionLocal()
                try:
                    try:
                        success = update_user_profile(db, user_id=user_id, full_name=full_name_val,
                                                      display_name=display_name_val, phone=phone_val, bio=bio_val)
                    except ValueError as ve:
                        st.error(str(ve))
                        success = False

                    if success:
                        st.success("Profile updated successfully.")
                        # hide the form after save and refresh values
                        st.session_state["editing_profile"] = False
                        st.rerun()
                    else:
                        st.error("Failed to update profile.")
                except Exception as e:
                    st.error(f"Error updating profile: {e}")
                finally:
                    db.close()

# Profile Picture Section
st.subheader("Profile Picture")

# Load existing profile picture
profile_pic_path = load_profile_picture(user_id)

# Display current profile picture
col1, col2 = st.columns([1, 2])
with col1:
    if profile_pic_path:
        st.image(profile_pic_path, width=150, caption="Current Profile Picture")
        # remove picture flow
        if st.button("Remove picture", key=f"remove_pic_{user_id}"):
            st.session_state[f"confirm_remove_pic_{user_id}"] = True

        if st.session_state.get(f"confirm_remove_pic_{user_id}", False):
            st.warning("Are you sure you want to remove your profile picture?")
            c_yes, c_no = st.columns([1, 1])
            if c_yes.button("Yes, remove", key=f"yes_remove_{user_id}"):
                db = SessionLocal()
                try:
                    try:
                        success = delete_user_profile_picture(db, user_id)
                    except Exception as de:
                        st.error(f"Error removing profile picture: {de}")
                        success = False
                    if success:
                        st.success("Profile picture removed.")
                        st.session_state.pop(f"confirm_remove_pic_{user_id}", None)
                        st.rerun()
                    else:
                        st.error("Could not remove profile picture.")
                finally:
                    db.close()
            if c_no.button("Cancel", key=f"no_remove_{user_id}"):
                st.session_state.pop(f"confirm_remove_pic_{user_id}", None)
                st.info("Removal cancelled.")
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
            # Preview before saving
            st.image(uploaded_file, width=200, caption="Preview")
            if st.button("Save Profile Picture"):
                try:
                    # Save the new profile picture
                    new_profile_path = save_profile_picture(uploaded_file, user_id)
                    # Persist profile picture path to user record
                    db = SessionLocal()
                    try:
                        update_user_profile(db, user_id=user_id, profile_picture=new_profile_path)
                    finally:
                        db.close()

                    # Remove old profile pictures
                    upload_dir = "uploads/profile_pictures"
                    for file in os.listdir(upload_dir):
                        if file.startswith(f"profile_{user_id}") and file != os.path.basename(new_profile_path):
                            try:
                                os.remove(os.path.join(upload_dir, file))
                            except OSError:
                                pass

                    st.success("Profile picture updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving profile picture: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# --- Messages Section ---
st.markdown('<div class="listings-container">', unsafe_allow_html=True)
st.header("💬 Messages Received")

db = SessionLocal()
try:
    messages = get_received_messages(db, user_id)
    if not messages:
        st.info("You have no messages yet.")
    else:
        for msg in messages:
            listing = db.query(Listing).filter(Listing.id == msg.listing_id).first()
            listing_title = listing.title if listing else "Listing Deleted"

            sender_name = getattr(msg.sender, "display_name", f"User {msg.sender_id}")
            
            st.markdown(f"""
            <div class="message-card">
                <b>From:</b> User {msg.sender_id} <br>
                <b>Regarding:</b> {listing_title} <br>
                <b>Message:</b> {msg.content} <br>
                <i>Sent on {msg.created_at.strftime('%b %d, %Y %I:%M %p')}</i>
            </div>
            """, unsafe_allow_html=True)
finally:
    db.close()
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