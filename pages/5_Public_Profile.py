# pages/5_Public_Profile.py
import streamlit as st
import os
from app.db import SessionLocal
from app.models.user import User
from app.models.listing import Listing
from app.models.image import Image
from app.models.review import Review
from app.crud.reviews import (
    get_reviews_for_user, get_user_average_rating, create_review,
    has_user_reviewed, update_review, delete_review
)
from sqlalchemy import select

st.set_page_config(page_title="Public Profile - Campus Market", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #005035; }
    .profile-container {
        background-color: #87B481;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .profile-header {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .profile-pic {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid white;
    }
    .profile-pic-placeholder {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: #005035;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 48px;
        font-weight: bold;
        border: 4px solid white;
    }
    .profile-info h1 { margin: 0; color: #005035; }
    .profile-info .rating { font-size: 1.1em; color: #2E7D32; }
    .listings-container {
        background-color: #87B481;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .reviews-container {
        background-color: #87B481;
        padding: 20px;
        border-radius: 10px;
    }
    .review-card {
        background-color: #E8F5E8;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #005035;
    }
    .review-header { font-weight: bold; color: #005035; margin-bottom: 5px; }
    .review-rating { color: #FF9800; font-weight: bold; }
    .review-comment { color: #333; margin-top: 5px; }
    .review-date { font-size: 0.85em; color: #666; font-style: italic; }
    .listing-card {
        background-color: #E8F5E8;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #005035;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Get user_id from URL query params or session state
query_params = st.query_params
raw_user_id = query_params.get("user_id")

# Handle Streamlit returning list values for query params
try:
    query_params = st.query_params
    raw_user_id = query_params.get("user_id")
except Exception:
    raw_user_id = None

if isinstance(raw_user_id, list):
    user_id_val = raw_user_id[0] if raw_user_id else None
else:
    user_id_val = raw_user_id

# Fallback to session state if not in query params
if not user_id_val:
    user_id_val = st.session_state.get("public_profile_user_id")

if not user_id_val:
    st.error("No user specified. Please view a user profile from a listing.")
    st.stop()

try:
    user_id = int(user_id_val)
except (ValueError, TypeError):
    st.error("Invalid user ID.")
    st.stop()

db = SessionLocal()

try:
    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        st.error("User not found.")
        st.stop()

    # --- Header Section ---
    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="profile-header">', unsafe_allow_html=True)
    
    # Profile picture: try multiple candidate paths (absolute, relative, uploads folder)
    profile_pic_path = None
    if user.profile_picture:
        candidates = [
            user.profile_picture,
            os.path.join(os.getcwd(), user.profile_picture),
            os.path.join(os.getcwd(), "uploads", "profile_pictures", user.profile_picture),
        ]
        for p in candidates:
            try:
                if p and os.path.exists(p):
                    profile_pic_path = p
                    break
            except Exception:
                continue

    if profile_pic_path:
        try:
            st.image(profile_pic_path, width=120)
        except Exception:
            # fallback to placeholder
            display_name = user.full_name or user.display_name or f"User {user.id}"
            st.markdown(f'<div class="profile-pic-placeholder">{display_name[0].upper()}</div>', unsafe_allow_html=True)
    else:
        display_name = user.full_name or user.display_name or f"User {user.id}"
        st.markdown(f'<div class="profile-pic-placeholder">{display_name[0].upper()}</div>', unsafe_allow_html=True)
    
    # Profile info - prefer full_name for clearer display
    display_name = user.full_name or user.display_name or f"User {user.id}"
    avg_rating = get_user_average_rating(db, user.id)
    rating_text = f"⭐ {avg_rating:.1f}" if avg_rating else "No ratings yet"
    
    st.markdown(f"""
    <div class="profile-info">
        <h1>{display_name}</h1>
        <div class="rating">{rating_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # end profile-header
    
    # Bio
    if user.bio:
        st.markdown(f"**Bio:** {user.bio}")
    
    st.markdown('</div>', unsafe_allow_html=True)  # end profile-container

    # --- Listings Section ---
    st.markdown('<div class="listings-container">', unsafe_allow_html=True)
    st.header("📋 Listings by this User")
    
    user_listings = db.query(Listing).filter(Listing.user_id == user.id).all()
    
    if not user_listings:
        st.write("This user has no listings.")
    else:
        st.write(f"**Total Listings:** {len(user_listings)}")
        for listing in user_listings:
            st.markdown(f"""
            <div class="listing-card">
                <strong>{listing.title}</strong><br>
                Price: ${listing.price:.2f}<br>
                Condition: {listing.category}<br>
                Description: {listing.description}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Reviews Section ---
    st.markdown('<div class="reviews-container">', unsafe_allow_html=True)
    st.header("⭐ Reviews")
    
    reviews = get_reviews_for_user(db, user.id)
    
    if not reviews:
        st.write("No reviews yet for this user.")
    else:
        for review in reviews:
            reviewer_name = review.reviewer.display_name or review.reviewer.full_name or f"User {review.reviewer_id}"
            st.markdown(f"""
            <div class="review-card">
                <div class="review-header">{reviewer_name}</div>
                <div class="review-rating">Rating: {'⭐' * int(review.rating)} ({review.rating}/5.0)</div>
                <div class="review-comment">{review.comment or "No comment"}</div>
                <div class="review-date">Reviewed on {review.created_at.strftime('%B %d, %Y')}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Leave a Review Section ---
    st.markdown('<div class="reviews-container">', unsafe_allow_html=True)
    st.header("Leave a Review")
    
    current_user_id = st.session_state.get("user_id")
    
    if not current_user_id:
        st.info("Please log in to leave a review.")
    elif current_user_id == user.id:
        st.warning("You cannot review yourself.")
    else:
        # Check if user has already reviewed
        already_reviewed = has_user_reviewed(db, current_user_id, user.id)
        
        if already_reviewed:
            existing_review = db.query(Review).filter(
                Review.reviewer_id == current_user_id,
                Review.reviewed_user_id == user.id
            ).first()
            st.info("You have already reviewed this user. You can update your review below.")
            
            # Show update form
            with st.form(key=f"update_review_{user.id}"):
                rating = st.slider("Rating", 1.0, 5.0, value=existing_review.rating, step=0.5)
                comment = st.text_area("Review Comment", value=existing_review.comment or "", height=100)
                submit = st.form_submit_button("Update Review")
                
                if submit:
                    try:
                        update_review(db, existing_review.id, rating=rating, comment=comment)
                        st.success("Review updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating review: {e}")
        else:
            # Show create form
            with st.form(key=f"create_review_{user.id}"):
                rating = st.slider("Rating", 1.0, 5.0, value=3.0, step=0.5)
                comment = st.text_area("Review Comment (optional)", height=100)
                submit = st.form_submit_button("Submit Review")
                
                if submit:
                    if not rating:
                        st.error("Please select a rating.")
                    else:
                        try:
                            create_review(
                                db,
                                reviewer_id=current_user_id,
                                reviewed_user_id=user.id,
                                rating=rating,
                                comment=comment if comment.strip() else None
                            )
                            st.success("Review submitted successfully!")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"Error: {e}")
                        except Exception as e:
                            st.error(f"An error occurred: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

finally:
    db.close()
