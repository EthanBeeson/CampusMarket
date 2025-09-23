import streamlit as st
import hashlib
from datetime import datetime

# SQLAlchemy imports
from app.db import Base, engine, SessionLocal
from sqlalchemy import Column, Integer, String, DateTime, select

# Use the shared Base from app.db
ORMBase = Base

# Define User model safely for Streamlit reruns
if "User" not in globals():
    class User(ORMBase):
        __tablename__ = "users"
        __table_args__ = {"extend_existing": True}  # <-- prevent duplicate table errors

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
st.set_page_config(page_title="Login - Campus Market", layout="centered")
st.title("🔑 Login")

st.write("Please sign in with your student email and password.")

with st.form("login_form"):
    email = st.text_input("Student Email", placeholder="you@uncc.edu")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in")

    if submitted:
        if not email.strip():
            st.error("Please enter your student email.")
        elif not is_student_email(email.strip()):
            st.error("Please enter a valid student email (must be a .edu address).")
        elif not password:
            st.error("Please enter your password.")
        else:
            db = SessionLocal()
            try:
                user = find_user_by_email(db, email.strip().lower())
                if not user:
                    st.error("No account found with that email. Go to the Signup page to create one.")
                    st.info("Tip: Click the 'Signup' page in the top-right menu to register.")
                elif user.password_hash == hash_password(password):
                    st.success("Login successful 🎉")
                    st.balloons()
                    st.session_state["user_email"] = user.email
                    st.session_state["user_id"] = user.id
                else:
                    st.error("Incorrect password. Try again or reset your password.")
            finally:
                db.close()