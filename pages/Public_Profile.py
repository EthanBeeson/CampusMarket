# pages/Public_Profile.py
import streamlit as st
import os
from PIL import Image as PILImage
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
import json
from datetime import datetime

st.set_page_config(page_title="Public Profile - Campus Market", layout="wide")

st.markdown(
    """
    <style>
        /* Global background */
        .stApp { background-color: #ffffff !important; }
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

    # --- Profile Header (simple, no card container) ---
    display_name = user.full_name or user.display_name or f"User {user.id}"
    avg_rating = get_user_average_rating(db, user.id)
    rating_text = f"⭐ {avg_rating:.1f}" if avg_rating else "No ratings yet"
    
    st.title(display_name)
    st.markdown(f"**Rating:** {rating_text}")
    
    if user.bio:
        st.markdown(f"**Bio:** {user.bio}")
    
    st.divider()

    # current viewer
    current_user_id = st.session_state.get("user_id")

    # --- Listings Section ---
    st.header("📋 Listings by this User")
    
    user_listings = db.query(Listing).filter(Listing.user_id == user.id).all()
    
    if not user_listings:
        st.write("This user has no listings.")
    else:
        st.write(f"**Total Listings:** {len(user_listings)}")
        
        for listing in user_listings:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # Title
            st.markdown(
                f"<h2 class='center'>{listing.title} - ${float(listing.price):.2f}</h2>",
                unsafe_allow_html=True,
            )
            
            # Meta
            condition = getattr(listing, "condition", "Unknown")
            st.markdown(f"<p class='center'><b>Condition:</b> {condition}</p>", unsafe_allow_html=True)
            
            if listing.description:
                st.markdown(f"<p class='center'>{listing.description}</p>", unsafe_allow_html=True)
            
            # Image carousel
            if listing.images:
                key_idx = f"img_idx_{listing.id}"
                if key_idx not in st.session_state:
                    st.session_state[key_idx] = 0
                
                img_idx = st.session_state[key_idx]
                total = len(listing.images)
                try:
                    img_path = listing.images[img_idx].url
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

            # Report flow for public listings
            if listing.user_id != current_user_id:
                if st.button("🚩 Report Listing", key=f"pub_report_{listing.id}", use_container_width=True):
                    st.session_state[f"pub_report_open_{listing.id}"] = True

                if st.session_state.get(f"pub_report_open_{listing.id}", False):
                    reason = st.text_area("Why are you reporting this listing? (optional)", key=f"pub_report_reason_{listing.id}", height=80)
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        if st.button("Submit Report", key=f"pub_report_submit_{listing.id}"):
                            try:
                                # persist to reports JSONL
                                os.makedirs("reports", exist_ok=True)
                                report = {
                                    "listing_id": int(listing.id),
                                    "reporter_id": int(current_user_id) if current_user_id is not None else None,
                                    "reason": reason or "",
                                    "timestamp": datetime.utcnow().isoformat() + "Z",
                                }
                                with open(os.path.join("reports", "reports.jsonl"), "a", encoding="utf-8") as fh:
                                    fh.write(json.dumps(report, ensure_ascii=False) + "\n")
                                st.success("Thanks — the listing has been reported.")
                                st.session_state.pop(f"pub_report_open_{listing.id}", None)
                            except Exception as e:
                                st.error(f"Error saving report: {e}")
                    with c2:
                        if st.button("Cancel", key=f"pub_report_cancel_{listing.id}"):
                            st.session_state.pop(f"pub_report_open_{listing.id}", None)
            
            st.markdown('</div>', unsafe_allow_html=True)  # end card

    # --- Reviews Section ---
    st.divider()
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
    
    st.divider()

    # --- Leave a Review Section ---
    st.header("Leave a Review")
    
    current_user_id = st.session_state.get("user_id")
    
    if not current_user_id:
        st.info("Please log in to leave a review.")
    elif current_user_id == user.id:
        st.warning("You cannot review yourself.")
    else:
        # Show create form (only check for existing review if form is submitted)
        with st.form(key=f"create_review_{user.id}"):
            rating = st.slider("Rating", 1.0, 5.0, value=3.0, step=0.5)
            comment = st.text_area("Review Comment (optional)", height=100)
            submit = st.form_submit_button("Submit Review")
            
            if submit:
                # Check if user has already reviewed after form submission
                already_reviewed = has_user_reviewed(db, current_user_id, user.id)
                
                if already_reviewed:
                    st.warning("You have already reviewed this user. Update your review instead.")
                    # Show update form option
                    existing_review = db.query(Review).filter(
                        Review.reviewer_id == current_user_id,
                        Review.reviewed_user_id == user.id
                    ).first()
                    st.info("You can update your review below.")
                else:
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
        
        # Show update form if user has already reviewed
        if has_user_reviewed(db, current_user_id, user.id):
            existing_review = db.query(Review).filter(
                Review.reviewer_id == current_user_id,
                Review.reviewed_user_id == user.id
            ).first()
            st.divider()
            st.subheader("Update Your Review")
            
            # Show update form
            with st.form(key=f"update_review_{user.id}"):
                rating = st.slider("Rating", 1.0, 5.0, value=existing_review.rating, step=0.5, key="update_rating")
                comment = st.text_area("Review Comment", value=existing_review.comment or "", height=100, key="update_comment")
                submit = st.form_submit_button("Update Review")
                
                if submit:
                    try:
                        update_review(db, existing_review.id, rating=rating, comment=comment)
                        st.success("Review updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating review: {e}")

finally:
    db.close()
