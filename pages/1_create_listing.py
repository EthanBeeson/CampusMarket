# app/pages/1_Create_Listing.py

# UI Framework 
import streamlit as st
import os
import uuid

# SQLAlchemy DB Session 
from app.db import SessionLocal
# CRUD Function that writes a new listing to the database 
from app.crud.listings import create_listing, ALLOWED_CONDITIONS, ALLOWED_CATEGORIES

# Make sure we have a place to store uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Charlotte green background
st.markdown(
    """
    <style>
    /* Entire page background */
    .stApp {
        background-color: #005035;  /* dark green */
    }

    /* Form container background */
    div[data-testid="stForm"] {
        background-color: #87B481;  /* light green */
        padding: 20px;
        border-radius: 10px;
    }

    /* Input fields styling - typed text black and inputs white */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        background-color: white;
        color: black;               
        -webkit-text-fill-color: black;
    }

    /* Price box styling */
    .stNumberInput input {
        background-color: white !important;
        color: black !important;
    }

    /* Placeholder styling */
    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder,
    input::placeholder,
    textarea::placeholder {
        color: black !important;
        opacity: 1 !important;
    }

    /* Submit button */
    div.stButton > button {
        background-color: #4CAF50;  /* green button */
        color: white;
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

st.markdown("""<style> .stApp { background-color: #005035; } 
div[data-testid="stForm"] { background-color:#87B481; padding:20px; border-radius:10px; }
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{background:white;color:black;-webkit-text-fill-color:black;}
.stTextInput>div>div>input::placeholder,.stTextArea>div>div>textarea::placeholder,input::placeholder,textarea::placeholder{color:black!important;opacity:1!important;}
div.stButton > button { background-color:#4CAF50; color:white; }
</style>""", unsafe_allow_html=True)

st.title("Create Listing")

with st.form("create_listing_form", clear_on_submit=False):
    title = st.text_input("Title", max_chars=100, placeholder="e.g. Mini Fridge")
    description = st.text_area("Description", placeholder="e.g. Works well; pickup only.")
    # Condition selector (sourced from backend allowed list)
    condition = st.selectbox("Condition", ALLOWED_CONDITIONS, index=ALLOWED_CONDITIONS.index("Good") if "Good" in ALLOWED_CONDITIONS else 0)
    # Category selector (sourced from backend allowed list)
    category = st.selectbox("Category", ALLOWED_CATEGORIES, index=ALLOWED_CATEGORIES.index("Other") if "Other" in ALLOWED_CATEGORIES else 0)
    price = st.number_input("Price (USD)", min_value=0.0, step=1.0, format="%.2f")
    #contact = st.text_input("Contact Information", placeholder="Email and/or Phone Number")
    contact_email = st.text_input("Contact Email (optional)", placeholder="example@email.com")
    contact_phone = st.text_input("Contact Phone (optional)", placeholder="e.g. 555-123-4567")
    images = st.file_uploader(
        "Upload Item Pictures",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    submitted = st.form_submit_button("Publish")

    if submitted:
        errors = []
        if not title.strip():
            errors.append("Title is required.")
        if not description.strip():
            errors.append("Description is required.")
        if price is None or price < 0:
            errors.append("Price must be 0 or greater.")
        #if not contact.strip():
            #errors.append("Contact information is required.")
        if not contact_email.strip() and not contact_phone.strip():
            errors.append("At least one contact method (email or phone) is required.")


        if errors:
            for e in errors:
                st.error(e)
        else:
            # Save uploaded files
            saved_paths = []
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
                st.success(f"Listing created: {item.title}")
                if saved_paths:
                    #st.image(saved_paths, caption="Uploaded Images", use_column_width=True)
                    st.image(saved_paths, caption="Uploaded Images", use_container_width=True)
            finally:
                db.close()
