# app/pages/1_Create_Listing.py
#UI Framework 
import streamlit as st
#SQlAlchemy DB Session 
from app.db import SessionLocal
#CRUD Function that writes a new listing to the database 
from app.crud.listings import create_listing

st.title("Create Listing")

with st.form("create_listing_form", clear_on_submit=False):
    title = st.text_input("Title", max_chars=100, placeholder="Mini Fridge")
    description = st.text_area("Description", placeholder="Works well; pickup only.")
    price = st.number_input("Price (USD)", min_value=0.0, step=1.0, format="%.2f")
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