# app/pages/1_Create_Listing.py
#UI Framework 
import streamlit as st
#SQlAlchemy DB Session 
from app.db import SessionLocal
#CRUD Function that writes a new listing to the database 
from app.crud.listings import create_listing

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
        color: black;               /* typed text color */
        -webkit-text-fill-color: black; /* extra for some webkit cases */
    }

    /* CHANGED: Ensure NumberInput (Price box) matches styling */
    .stNumberInput input {
        background-color: white !important;
        color: black !important;
    }

    /* CHANGED: placeholder styling for many browsers and cases */
    /* WebKit/Blink */
    .stTextInput>div>div>input::-webkit-input-placeholder,
    .stTextArea>div>div>textarea::-webkit-input-placeholder,
    input::-webkit-input-placeholder,
    textarea::-webkit-input-placeholder {
        color: black !important;
        opacity: 1 !important;
    }

    /* Firefox 19+ */
    .stTextInput>div>div>input::-moz-placeholder,
    .stTextArea>div>div>textarea::-moz-placeholder,
    input::-moz-placeholder,
    textarea::-moz-placeholder {
        color: black !important;
        opacity: 1 !important;
    }

    /* IE 10+ */
    .stTextInput>div>div>input:-ms-input-placeholder,
    .stTextArea>div>div>textarea:-ms-input-placeholder,
    input:-ms-input-placeholder,
    textarea:-ms-input-placeholder {
        color: black !important;
        opacity: 1 !important;
    }

    /* Standard */
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

st.title("Create Listing")

with st.form("create_listing_form", clear_on_submit=False):
    title = st.text_input("Title", max_chars=100, placeholder="e.g. Mini Fridge")
    description = st.text_area("Description", placeholder="e.g. Works well; pickup only.")
    price = st.number_input("Price (USD)", min_value=0.0, step=1.0, format="%.2f")
    contact = st.text_input("Contact Information", placeholder="Email and/or Phone Number")
    submitted = st.form_submit_button("Publish")

    #validation for title/description/price 
    if submitted:
        errors = []
        if not title.strip():
            errors.append("Title is required.")
        if not description.strip():
            errors.append("Description is required.")
        if price is None or price < 0:
            errors.append("Price must be 0 or greater.")
        if not contact.strip():
            errors.append("Contact information is required.")

    #displays visible error messages - this is where if valid opens a DB session and calls crud
        if errors:
            for e in errors:
                st.error(e)
        else:
            db = SessionLocal()
            try:
                item = create_listing(
                    db=db,
                    title=title.strip(),
                    description=description.strip(),
                    price=price,         # your model uses Float now
                    image_urls=[],       # hook up later when you add uploads
                )
                st.success(f"Listing created: {item.title}")
            finally:
                db.close()