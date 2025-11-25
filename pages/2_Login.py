# pages/2_Login.py
import streamlit as st
from app.db import SessionLocal
from app.crud.users import authenticate_user, validate_charlotte_email

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Login - Campus Market", layout="centered")

st.markdown(
    """
    <style>
        /* Global background */
        .stApp { background-color: #fffdf2 !important; }
        .block-container { max-width: 900px; margin: 0 auto; }

        /* 1) Main content text (title, body, caption) */
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
            color: #333333 !important;    /* readable grey body text */
        }

        /* Caption text from st.caption */
        div[data-testid="stAppViewContainer"] .stCaption,
        div[data-testid="stAppViewContainer"] .stMarkdown small,
        div[data-testid="stAppViewContainer"] .stMarkdown .caption {
            color: #666666 !important;    /* softer grey for captions */
        }

        /* 2) Sidebar: keep text white */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] .stMarkdown {
            color: #ffffff !important;
        }

        /* 3) Inputs (text + password) */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #000000 !important;               /* black typed text */
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }
        .stTextInput > div > div > input::placeholder { color: #666666 !important; }
        .stTextInput > div > div > input:focus {
            border-color: #003d28 !important;
            box-shadow: 0 0 0 3px rgba(0, 80, 53, 0.1) !important;
        }
        .stTextInput input[type="password"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }

        /* 4) Buttons: keep text white */
        div.stButton > button,
        .stFormSubmitButton > button {
            background-color: #005035 !important;
            color: #ffffff !important;               /* button text white */
            border: 2px solid #005035 !important;
            border-radius: 10px !important;
            padding: 10px 14px !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin-top: 15px !important;
        }

        /* Ensure all inner text nodes inside BOTH buttons stay white */
        div.stButton > button *,
        .stFormSubmitButton > button * {
            color: #ffffff !important;               /* override grey span inside buttons */
        }

        /* Hover effect */
        div.stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background-color: #003d28 !important;
            border-color: #003d28 !important;
        }

        /* 5) Notifications/messages — readable text */
        div[data-testid="stNotification"] {
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            background-color: #ffffff !important;
        }
        div[data-testid="stNotification"] p,
        div[data-testid="stNotification"] span,
        div[data-testid="stNotification"] div {
            color: #000000 !important;               /* message text black */
            font-weight: 600 !important;
        }
        /* Error (role=alert) background + border */
        div[role="alert"] {
            background-color: rgba(211, 47, 47, 0.12) !important;
            border: 1px solid #d32f2f !important;
            border-radius: 8px !important;
        }
        /* Success/info (non-alert) background + border */
        div[data-testid="stNotification"]:not([role="alert"]) {
            background-color: rgba(0, 80, 53, 0.12) !important;
            border: 1px solid #005035 !important;
            border-radius: 8px !important;
        }

        /* 6) Horizontal rule */
        hr { border-color: #cccccc !important; }
        
        /* Final fix: Log in button text stays white */
        div[data-testid="stAppViewContainer"] .stFormSubmitButton > button,
        div[data-testid="stAppViewContainer"] .stFormSubmitButton > button * {
            color: #ffffff !important;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Login")
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
                        st.session_state["user_email"] = user.email
                        st.session_state["user_id"] = user.id
                        st.session_state["authenticated"] = True
                        st.success("Login successful! 🎉")
                        st.balloons()
                        st.switch_page("pages/4_Profile.py")
                finally:
                    db.close()

# Password reset navigation
st.write("---")
if st.button("Forgot your password? Reset it here"):
    st.switch_page("pages/7_Reset_Password.py")
