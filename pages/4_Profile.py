# app/pages/4_Profile.py
import streamlit as st
import os
import re
from PIL import Image as PILImage
import io
import base64
import json
from datetime import datetime

# SQLAlchemy imports
from app.db import SessionLocal
from sqlalchemy import select
from app.models.listing import Listing
from app.models.image import Image
from app.models.user import User
from app.crud.users import (
    update_user_profile,
    delete_user_profile_picture,
    update_user_password,
    verify_user_password,
)
from app.models.message import Message
from app.crud.favorites import is_favorited, add_favorite, remove_favorite, get_user_favorites
from app.models.favorite import Favorite

st.divider()

# Charlotte colors styling
st.markdown(
    """
    <style>
        /* Global background */
        .stApp { background-color: #fffdf2 !important; }
        .block-container { max-width: 900px; margin: 0 auto; }

        /* Headings and main content text */
        div[data-testid="stAppViewContainer"] h1,
        div[data-testid="stAppViewContainer"] h2,
        div[data-testid="stAppViewContainer"] h3,
        div[data-testid="stAppViewContainer"] h4,
        div[data-testid="stAppViewContainer"] h5,
        div[data-testid="stAppViewContainer"] h6 {
            color: #005035 !important;   /* Charlotte green headings */
        }
        div[data-testid="stAppViewContainer"] .stMarkdown,
        div[data-testid="stAppViewContainer"] p,
        div[data-testid="stAppViewContainer"] span,
        div[data-testid="stAppViewContainer"] label,
        div[data-testid="stAppViewContainer"] div:not([data-testid="stSidebar"]) {
            color: #333333 !important;   /* readable grey body text */
        }
        div[data-testid="stAppViewContainer"] .stCaption {
            color: #666666 !important;   /* softer grey captions */
        }

        /* Sidebar text stays white */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] .stMarkdown {
            color: #ffffff !important;
        }

        /* Cards and profile container */
        .card {
            background: #f9f9f9 !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 14px !important;
            padding: 18px 20px !important;
            margin: 18px 0 26px 0 !important;
        }
        .card h2, .card h3, .card p { margin: 6px 0 !important; }
        .center { text-align: center !important; }
        .profile-container {
            background-color: rgba(135, 180, 129, 0.15) !important;
            padding: 20px !important;
            border-radius: 10px !important;
            margin-bottom: 20px !important;
        }

        /* Inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: #666666 !important;
            opacity: 1 !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #003d28 !important;
            box-shadow: 0 0 0 3px rgba(0, 80, 53, 0.1) !important;
        }

        /* Buttons: Charlotte green with white text */
        div.stButton > button,
        .stFormSubmitButton > button {
            background-color: #005035 !important;
            color: #ffffff !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 10px 14px !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin-top: 15px !important;
        }
        div.stButton > button *,
        .stFormSubmitButton > button * {
            color: #ffffff !important;
        }
        div.stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background-color: #003d28 !important;
            border-color: #003d28 !important;
        }

        /* Listing date style */
        .listing-date {
            color: #666666 !important;
            font-size: 0.9em !important;
            font-style: italic !important;
        }

        /* Notifications/messages */
        div[data-testid="stNotification"] {
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            background-color: #ffffff !important;
        }
        div[data-testid="stNotification"] p,
        div[data-testid="stNotification"] span,
        div[data-testid="stNotification"] div {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        div[role="alert"] {
            background-color: rgba(211, 47, 47, 0.12) !important;
            border: 1px solid #d32f2f !important;
            border-radius: 8px !important;
        }
        div[data-testid="stNotification"]:not([role="alert"]) {
            background-color: rgba(0, 80, 53, 0.12) !important;
            border: 1px solid #005035 !important;
            border-radius: 8px !important;
        }

        /* Horizontal rule */
        hr { border-color: #cccccc !important; }

         /* Force all button labels to white */
        div.stButton > button,
        div.stButton > button *,
        .stFormSubmitButton > button,
        .stFormSubmitButton > button * {
            color: #ffffff !important;
        }
        /* Password input */
        .stTextInput input[type="password"] {
            background-color: #ffffff !important;
            color: #000000 !important;          /* typed text black */
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }
        .stTextInput input[type="password"]::placeholder {
            color: #666666 !important;          /* placeholder grey */
        }

        /* File uploader */
        [data-testid="stFileUploader"] section div div {
            color: #000000 !important;          /* label text black */
        }
        [data-testid="stFileUploader"] section div div::placeholder {
            color: #666666 !important;
        }
        [data-testid="stFileUploader"] section {
            background-color: #ffffff !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }
        /* Force Update Password button text white */
        div[data-testid="stAppViewContainer"] .stFormSubmitButton > button,
        div[data-testid="stAppViewContainer"] .stFormSubmitButton > button * {
            color: #ffffff !important;
        }
        /* Force Browse files text black/white depending on background */
        [data-testid="stFileUploader"] div,
        [data-testid="stFileUploader"] span,
        [data-testid="stFileUploader"] label {
            color: #000000 !important;   /* black text for readability */
        }
        [data-testid="stFileUploader"] section {
            background-color: #ffffff !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }


    </style>
    """,
    unsafe_allow_html=True,
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


def avatar_data_uri(path):
    """Return a data URI for an image file path (base64)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        mime = "image/png"
        if path.lower().endswith(".jpg") or path.lower().endswith(".jpeg"):
            mime = "image/jpeg"
        elif path.lower().endswith(".gif"):
            mime = "image/gif"
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception:
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
            st.error("You are not authorized to delete this listing.")
            return False
        
        # Get associated images
        images = db.query(Image).filter(Image.listing_id == listing_id).all()
        
        # Delete associated images
        for img in images:
            if os.path.exists(img.url):
                try:
                    os.remove(img.url)
                    st.info(f"Deleted image: {os.path.basename(img.url)}")
                except OSError as e:
                    st.warning(f"Could not delete image file: {e}")
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


def save_report(listing_id, reporter_id, reason: str = ""):
    """Save a simple JSON-lines report to the `reports/` folder.

    This avoids DB schema changes for now and produces a traceable record:
    `reports/reports.jsonl` where each line is a JSON object.
    """
    os.makedirs("reports", exist_ok=True)
    report = {
        "listing_id": int(listing_id),
        "reporter_id": int(reporter_id) if reporter_id is not None else None,
        "reason": reason or "",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    out_path = os.path.join("reports", "reports.jsonl")
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(report, ensure_ascii=False) + "\n")
    return out_path

def display_listing_card(listing, images, current_user_id):
    """Display a listing card with image carousel, date/time, and delete button"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Title
    st.markdown(
        f"<h2 class='center'>{listing.title} - ${float(listing.price):.2f}</h2>",
        unsafe_allow_html=True,
    )
    
    # Condition
    condition = getattr(listing, "condition", "Unknown")
    st.markdown(f"<p class='center'><b>Condition:</b> {condition}</p>", unsafe_allow_html=True)
    
    # Description
    if listing.description:
        st.markdown(f"<p class='center'>{listing.description}</p>", unsafe_allow_html=True)
    
    # Date/Time (kept from original)
    st.markdown(f"<p class='center listing-date'>Posted on {listing.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>", unsafe_allow_html=True)
    
    # Image carousel
    if images:
        key_idx = f"img_idx_{listing.id}"
        if key_idx not in st.session_state:
            st.session_state[key_idx] = 0
        
        img_idx = st.session_state[key_idx]
        total = len(images)
        try:
            img_path = images[img_idx].url
            img = PILImage.open(img_path).convert("RGB")
        except FileNotFoundError:
            img = None
            st.warning("[Image not found]")
        except Exception as e:
            img = None
            st.error(f"Error displaying image: {e}")
        
        # center the image in a fixed middle column
        L, M, R = st.columns([1, 2, 1])
        with M:
            if img is not None:
                st.image(img, use_container_width=True)
            
            # SINGLE centered button to advance
            bL, bC, bR = st.columns([2, 1, 2])
            with bC:
                if st.button("->", key=f"next_{listing.id}", use_container_width=True):
                    st.session_state[key_idx] = (img_idx + 1) % total
                    st.rerun()
        
        st.markdown(
            f"<p class='center' style='color:rgba(255,255,255,0.6)'>Image {img_idx + 1} of {total}</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<p class='center' style='opacity:.8'>No images available for this listing.</p>", unsafe_allow_html=True)
    
    # Delete button (only for owner)
    if listing.user_id == current_user_id:
        unique_delete_key = f"delete_{listing.id}_{listing.user_id}"
        if st.button("🗑️Delete My Listing", key=unique_delete_key, use_container_width=True):
            if delete_listing_safe(listing.id, current_user_id):
                st.rerun()

    # Report flow (visible to users who are not the owner)
    if listing.user_id != current_user_id:
        # Open the inline report form when user clicks Report
        if st.button("🚩 Report Listing", key=f"report_{listing.id}", use_container_width=True):
            st.session_state[f"report_open_{listing.id}"] = True

        if st.session_state.get(f"report_open_{listing.id}", False):
            reason = st.text_area("Why are you reporting this listing? (optional)", key=f"report_reason_{listing.id}", height=80)
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Submit Report", key=f"report_submit_{listing.id}"):
                    try:
                        save_report(listing.id, current_user_id, reason)
                        st.success("Thanks — the listing has been reported.")
                        # close the form
                        st.session_state.pop(f"report_open_{listing.id}", None)
                    except Exception as e:
                        st.error(f"Error saving report: {e}")
            with c2:
                if st.button("Cancel", key=f"report_cancel_{listing.id}"):
                    st.session_state.pop(f"report_open_{listing.id}", None)

    # --- Favorite button for non-owner ---
    if listing.user_id != current_user_id and "user_id" in st.session_state:
        db = SessionLocal()  # open db session
        favorited = is_favorited(db, current_user_id, listing.id)  # check if already favorited

        # Heart label: red if favorited, white if not
        heart_label = "❤️" if favorited else "🤍"

        # Button with unique key for profile
        if st.button(heart_label, key=f"profile_fav_{listing.id}", use_container_width=True):
            if favorited:
                remove_favorite(db, current_user_id, listing.id)
            else:
                add_favorite(db, current_user_id, listing.id)
            db.close()
            st.rerun()

        db.close()

    
    st.markdown('</div>', unsafe_allow_html=True)  # end card

# Main Profile Page
st.set_page_config(page_title="Profile - Campus Market", layout="wide")

# Check if user is logged in
if "user_id" not in st.session_state or "user_email" not in st.session_state:
    st.error("Please log in to view your profile.")
    st.stop()

user_id = st.session_state["user_id"]
user_email = st.session_state["user_email"]

# Header row: title on the left, profile picture / uploader on the right
col_title, col_pic = st.columns([3, 1])
with col_title:
    st.title(" Your Profile")

    # Show the profile picture right below the title
    profile_pic_path = load_profile_picture(user_id)
    if profile_pic_path:
        st.image(profile_pic_path, width=120, caption="Profile")
        # removal flow next to the image
        if st.button("Remove picture", key=f"header_remove_pic_{user_id}"):
            st.session_state[f"confirm_remove_pic_{user_id}"] = True

        if st.session_state.get(f"confirm_remove_pic_{user_id}", False):
            st.warning("Are you sure you want to remove your profile picture?")
            c_yes, c_no = st.columns([1, 1])
            if c_yes.button("Yes, remove", key=f"header_yes_remove_{user_id}"):
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
            if c_no.button("Cancel", key=f"header_no_remove_{user_id}"):
                st.session_state.pop(f"confirm_remove_pic_{user_id}", None)
                st.info("Removal cancelled.")
    else:
        st.info("No profile picture uploaded yet.")

with col_pic:
    # show uploader only when no profile picture exists; after saving the uploader will disappear on rerun
    if not profile_pic_path:
        uploaded_file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"], key="header_profile_pic_uploader")
        if uploaded_file is not None:
            if uploaded_file.size > 5 * 1024 * 1024:
                st.error("Image too large (<5MB)")
            else:
                st.image(uploaded_file, width=120, caption="Preview")
                if st.button("Save", key=f"header_save_pic_{user_id}"):
                    try:
                        new_profile_path = save_profile_picture(uploaded_file, user_id)
                        db = SessionLocal()
                        try:
                            update_user_profile(db, user_id=user_id, profile_picture=new_profile_path)
                        finally:
                            db.close()

                        # cleanup old files
                        upload_dir = "uploads/profile_pictures"
                        for file in os.listdir(upload_dir):
                            if file.startswith(f"profile_{user_id}") and file != os.path.basename(new_profile_path):
                                try:
                                    os.remove(os.path.join(upload_dir, file))
                                except OSError:
                                    pass

                        st.success("Saved")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        # profile picture exists -> hide uploader
        st.write("")

# Profile Section
st.markdown('<div class="profile-container">', unsafe_allow_html=True)
st.header("Profile Information")

# Display user email (username)
st.write(f"**Email:** {user_email}")

# Load user record for profile fields
db_user = None
db = SessionLocal()
try:
    db_user = db.query(User).filter(User.id == user_id).first()
finally:
    db.close()

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

#COMMENTED OUT BECAUSE IT WAS REPLACED WITH A BUTTON IN QUICK ACTIONS

# # Change Password Section (requires current password)
# st.subheader("Change Password")
# st.caption("For security, you must enter your current password.")
# with st.form("change_password_form"):
#     current_pw = st.text_input("Current Password", type="password")
#     new_pw = st.text_input("New Password", type="password")
#     confirm_pw = st.text_input("Confirm New Password", type="password")
#     change_pw = st.form_submit_button("Update Password")

#     if change_pw:
#         if not current_pw:
#             st.error("Please enter your current password.")
#         elif not new_pw or not confirm_pw:
#             st.error("Please enter and confirm your new password.")
#         elif new_pw != confirm_pw:
#             st.error("New passwords do not match.")
#         else:
#             db = SessionLocal()
#             try:
#                 if not verify_user_password(db, user_id, current_pw):
#                     st.error("Current password is incorrect.")
#                 else:
#                     try:
#                         update_user_password(db, user_id, new_pw)
#                         st.success("Password updated successfully.")
#                     except ValueError as e:
#                         st.error(str(e))
#             finally:
#                 db.close()


st.divider()

# User's Listings Section
st.header("Your Listings")

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
        
        # Display each listing with image carousel
        for listing in user_listings:
            listing_images = get_listing_images(db, listing.id)
            display_listing_card(listing, listing_images, user_id)
            
finally:
    db.close()

# USER FAVORITES SECTION

st.header("Your Favorite Listings")

db = SessionLocal()

try:
    favorites = get_user_favorites(db, user_id)

    # Filter out any listing that belongs to the current user
    filtered_favorites = []
    for fav in favorites:
        listing = db.query(Listing).filter(Listing.id == fav.listing_id).first()
        if listing and listing.user_id != user_id:
            filtered_favorites.append(listing)

    if not favorites:
        st.info("You haven't favorited any listings yet.")
    else:
        for fav in favorites:
            listing = db.query(Listing).filter(Listing.id == fav.listing_id).first()

            if listing:
                listing_images = get_listing_images(db, listing.id)
                display_listing_card(listing, listing_images, user_id)

finally:
    db.close()


# Enhanced Quick Actions Section with Logout
st.markdown("---")
st.header("Quick Actions")

col1, col2, col3 , col4= st.columns(4)

with col1:
    if st.button("Create New Listing", use_container_width=True):
        st.switch_page("pages/1_create_listing.py")

with col2:
    if st.button("Browse Listings", use_container_width=True):
        st.switch_page("main.py")

with col3:
    # Enhanced Logout button with confirmation
    if st.button("Logout", use_container_width=True, type="secondary"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logged out successfully!")
        st.rerun()

with col4:
    if st.button("Reset Password",use_container_width=True):
        st.switch_page("pages/7_Reset_Password.py")