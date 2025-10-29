# pages/2_Login.py
import streamlit as st
from app.db import SessionLocal
from app.crud.users import authenticate_user, validate_charlotte_email

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Login - Campus Market", layout="centered")

# Charlotte colors
st.markdown(
    """
    <style>
    .stApp {
        background-color: #005035;
    }
    div[data-testid="stForm"] {
        background-color: #87B481;
        padding: 20px;
        border-radius: 10px;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        background-color: white;
        color: black;
    }
    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder {
        color: black !important;
        opacity: 1 !important;
    }
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔑 Login")

st.write("Please sign in with your Charlotte student email and password.")

# Check if user is already authenticated
if st.session_state.get("authenticated", False):
    st.success(f"✅ You are already logged in as {st.session_state.get('user_email', '')}")
    if st.button("Go to Profile"):
        st.switch_page("pages/4_Profile.py")
    st.stop()

with st.form("login_form"):
    email = st.text_input("Student Email", placeholder="you@charlotte.edu")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in")

    if submitted:
        if not email.strip():
            st.error("Please enter your student email.")
        else:
            # Validate Charlotte email
            is_valid_email, email_error = validate_charlotte_email(email)
            if not is_valid_email:
                st.error(email_error)
            elif not password:
                st.error("Please enter your password.")
            else:
                db = SessionLocal()
                try:
                    is_authenticated, user = authenticate_user(db, email.strip().lower(), password)
                    
                    if not user:
                        st.error("No account found with that email. Please sign up first.")
                    elif not is_authenticated:
                        st.error("Incorrect password. Please try again.")
                    else:
                        # Start session - store user info
                        st.session_state["user_email"] = user.email
                        st.session_state["user_id"] = user.id
                        st.session_state["authenticated"] = True
                        
                        st.success("Login successful! 🎉")
                        st.balloons()
                        st.switch_page("pages/4_Profile.py")
                        
                finally:
                    db.close()