# app/pages/1_Create_Listing.py

# UI Framework 
import streamlit as st
import os
import uuid
from app.storage import get_upload_subdir

# SQLAlchemy DB Session 
from app.db import SessionLocal
# CRUD Function that writes a new listing to the database 
from app.crud.listings import create_listing, ALLOWED_CONDITIONS, ALLOWED_CATEGORIES
from app.nav import render_nav_sidebar

# Make sure we have a place to store uploads
UPLOAD_DIR = get_upload_subdir("listing_images")

# Custom navigation sidebar
render_nav_sidebar()

# ======= CONSISTENT STYLING WITH MAIN PAGE ======= #
st.markdown(
    """
    <style>
    /* Global background */
    .stApp { background-color: #fffdf2 !important; }
    .block-container { max-width: 900px; margin: 0 auto; }

    /* Form container */
    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 2px solid #005035 !important;
        border-radius: 14px !important;
        padding: 30px !important;
        margin: 20px 0 !important;
        box-shadow: 0 4px 12px rgba(0, 80, 53, 0.1) !important;
    }

    /* Headings */
    h1 { color: #005035 !important; text-align: center; font-weight: bold; }
    .stMarkdown h3 { color: #005035 !important; font-weight: 600 !important; }

    /* Labels and text */
    label, .stMarkdown, .stText, .stNumberInput label, .stTextInput label, .stTextArea label {
        color: #333333 !important;
        font-weight: 600 !important;
    }

    /* Input fields */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input,
    input[type="number"], input[type="text"] {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #005035 !important;
        border-radius: 8px !important;
        padding: 10px 12px !important;
    }

    /* Placeholder text */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    .stNumberInput input::placeholder {
        color: #666666 !important;
        opacity: 0.8 !important;
    }

    /* Selectbox styling */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 2px solid #005035 !important;
        border-radius: 8px !important;
        color: #333333 !important;
        min-height: 42px !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #003d28 !important;
        box-shadow: 0 0 0 1px #003d28 !important;
    }
    div[data-baseweb="select"]:focus-within > div {
        border-color: #005035 !important;
        box-shadow: 0 0 0 2px rgba(0, 80, 53, 0.2) !important;
    }
    div[data-baseweb="select"] div[aria-hidden="true"] {
        color: #666666 !important; opacity: 0.8 !important;
    }
    div[data-baseweb="select"] div[role="button"] {
        color: #333333 !important; font-weight: 500 !important;
    }
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 1px solid #005035 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 80, 53, 0.15) !important;
    }
    div[data-baseweb="menu"] li {
        background-color: #ffffff !important;
        color: #333333 !important;
        padding: 10px 12px !important;
        font-size: 14px !important;
    }
    div[data-baseweb="menu"] li:hover {
        background-color: rgba(0, 80, 53, 0.1) !important;
        color: #005035 !important;
    }
    div[data-baseweb="menu"] li[aria-selected="true"] {
        background-color: #005035 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Buttons */
    div.stButton > button, .stFormSubmitButton > button {
        background-color: #005035 !important;
        color: #ffffff !important;
        border: 2px solid #005035 !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        width: 100% !important;
        font-size: 1.1em !important;
    }
    div.stButton > button:hover, .stFormSubmitButton > button:hover {
        background-color: #003d28 !important;
        border-color: #003d28 !important;
    }

    /* File uploader */
    .stFileUploader > div {
        border: 2px dashed #005035 !important;
        border-radius: 10px !important;
        background: rgba(0, 80, 53, 0.05) !important;
    }
    .stFileUploader > div > div > div { color: #333333 !important; }
    .stFileUploader > div button {
        background-color: #005035 !important;
        color: #ffffff !important;
        border: none !important;
    }

    /* Base notification box */
    div[data-testid="stNotification"] {
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }

    /* 1) Make ALL text inside notifications visible (failsafe) */
    div[data-testid="stNotification"] p,
    div[data-testid="stNotification"] span,
    div[data-testid="stNotification"] div {
        color: #333333 !important;   /* fallback readable color */
    }

    /* 2) Error: background + border + text color */
    div[data-testid="stNotification"] .stError {
        background-color: rgba(211, 47, 47, 0.12) !important;
        border: 1px solid #d32f2f !important;
        border-radius: 8px !important;
    }
    div[data-testid="stNotification"] .stError p,
    div[data-testid="stNotification"] .stError span,
    div[data-testid="stNotification"] .stError div {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* 3) Success: background + border + text color */
    div[data-testid="stNotification"] .stSuccess {
        background-color: rgba(0, 80, 53, 0.12) !important;
        border: 1px solid #005035 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stNotification"] .stSuccess p,
    div[data-testid="stNotification"] .stSuccess span,
    div[data-testid="stNotification"] .stSuccess div {
        color: #005035 !important;
        font-weight: 600 !important;
    }

    /* 4) Info: background + border + text color */
    div[data-testid="stNotification"] .stInfo {
        background-color: rgba(0, 80, 53, 0.12) !important;
        border: 1px solid #005035 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stNotification"] .stInfo p,
    div[data-testid="stNotification"] .stInfo span,
    div[data-testid="stNotification"] .stInfo div {
        color: #005035 !important;
        font-weight: 600 !important;
    }

    /* 5) Extra failsafe: target the ARIA alert node Streamlit uses */
    div[role="alert"] p,
    div[role="alert"] span,
    div[role="alert"] div {
        color: #000000 !important;    /* errors typically render in role="alert" */
        font-weight: 600 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# Require login
user_id = st.session_state.get("user_id")
if not user_id:
    st.info("Please log in to create a listing.")
    st.stop()


st.title("Create Listing")

with st.form("create_listing_form", clear_on_submit=True):
    # Form header with consistent styling
    st.markdown('<p style="color: #005035; font-size: 1.2em; margin-bottom: 20px;">Fill out the details below to create your listing</p>', unsafe_allow_html=True)
    
    title = st.text_input("Title", max_chars=100, placeholder="e.g. Mini Fridge - Excellent Condition")
    description = st.text_area("Description", placeholder="Describe your item... include details like condition, size, pickup availability, etc.")
    
    # Two columns for condition and category
    col1, col2 = st.columns(2)
    with col1:
        condition = st.selectbox("Condition", ALLOWED_CONDITIONS, index=ALLOWED_CONDITIONS.index("Good") if "Good" in ALLOWED_CONDITIONS else 0)
    with col2:
        category = st.selectbox("Category", ALLOWED_CATEGORIES, index=ALLOWED_CATEGORIES.index("Other") if "Other" in ALLOWED_CATEGORIES else 0)
    
    price = st.number_input("Price (USD)", min_value=0.0, step=1.0, format="%.2f", help="Enter 0 for free items")
    
    # Contact information in two columns
    st.markdown('<p style="color: #005035; font-weight: bold; margin-top: 20px;">Contact Information</p>', unsafe_allow_html=True)
    contact_col1, contact_col2 = st.columns(2)
    with contact_col1:
        contact_email = st.text_input("Contact Email", placeholder="your.email@uncc.edu")
    with contact_col2:
        contact_phone = st.text_input("Contact Phone (optional)", placeholder="(704) 123-4567")
    
    # File uploader
    st.markdown('<p style="color: #005035; font-weight: bold; margin-top: 20px;">Item Photos</p>', unsafe_allow_html=True)
    images = st.file_uploader(
        "Upload photos of your item",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload clear photos from different angles. Maximum 10 images."
    )

    # Submit button
    submitted = st.form_submit_button("Publish Listing")

    if submitted:
        errors = []
        if not title.strip():
            errors.append(" Title is required.")
        if not description.strip():
            errors.append(" Description is required.")
        if price is None or price < 0:
            errors.append(" Price must be 0 or greater.")
        if not contact_email.strip() and not contact_phone.strip():
            errors.append("At least one contact method (email or phone) is required.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # Save uploaded files
            saved_paths = []
            if images:
                for img in images:
                    ext = os.path.splitext(img.name)[1].lower()
                    filename = f"{uuid.uuid4().hex}{ext}"
                    file_path = os.path.join(UPLOAD_DIR, filename)

                    with open(file_path, "wb") as f:
                        f.write(img.getbuffer())

                    saved_paths.append(file_path)

            db = SessionLocal()
            try:
                item = create_listing(
                    db=db,
                    title=title.strip(),
                    description=description.strip(),
                    price=price,
                    condition=condition,
                    category=category,
                    image_urls=saved_paths,   # store local file paths in DB
                    user_id=user_id,
                )
                st.success(f" Listing created successfully: **{item.title}**")
                
                if saved_paths:
                    # Display images in centered carousel style matching main page
                    L, M, R = st.columns([1, 2, 1])
                    with M:
                        st.image(saved_paths, use_container_width=True)

                
            except Exception as e:
                st.error(f"❌ Error creating listing: {str(e)}")
            finally:
                db.close()
