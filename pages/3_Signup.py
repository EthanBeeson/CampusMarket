# app/pages/3_Signup.py
import streamlit as st
import hashlib
from datetime import datetime

# SQLAlchemy imports
from app.db import Base, engine, SessionLocal
from sqlalchemy import Column, Integer, String, DateTime, select

# Use the shared Base
ORMBase = Base

# Define User model safely (reuse same class as login)
if "User" not in globals():
    class User(ORMBase):
        __tablename__ = "users"
        __table_args__ = {"extend_existing": True}  # prevent duplicate table errors

        id = Column(Integer, primary_key=True, index=True)
        email = Column(String(256), unique=True, index=True, nullable=False)
        password_hash = Column(String(128), nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

# Ensure tables exist
ORMBase.metadata.create_all(bind=engine)

# ---------------- Utility functions ----------------
def hash_password(password: str) -> str:
    """Return SHA-256 hash of password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def is_student_email(email: str) -> bool:
    """Check if email is a valid student .edu email."""
    return bool(email) and "@" in email and (email.lower().endswith(".edu") or ".edu" in email.lower())

def find_user_by_email(db, email: str):
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalars().first()

def create_user(db, email: str, password: str):
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Signup - Campus Market", layout="centered")
st.title("📝 Signup")

st.write("Create a new account with your student email and password.")

with st.form("signup_form"):
    email = st.text_input("Student Email", placeholder="you@uncc.edu")
    password = st.text_input("Password", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")
    submitted = st.form_submit_button("Sign Up")

    if submitted:
        if not email.strip():
            st.error("Please enter your student email.")
        elif not is_student_email(email.strip()):
            st.error("Please enter a valid student email (must be a .edu address).")
        elif not password:
            st.error("Please enter a password.")
        elif password != password_confirm:
            st.error("Passwords do not match.")
        else:
            db = SessionLocal()
            try:
                existing_user = find_user_by_email(db, email.strip().lower())
                if existing_user:
                    st.error("An account with this email already exists. Please log in instead.")
                else:
                    user = create_user(db, email.strip().lower(), password)
                    st.success("Signup successful 🎉 You can now log in.")
                    # Optionally store user in session_state immediately
                    st.session_state["user_email"] = user.email
                    st.session_state["user_id"] = user.id
            finally:
                db.close()
