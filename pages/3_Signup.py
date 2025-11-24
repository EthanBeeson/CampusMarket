# pages/3_Signup.py
import streamlit as st
from app.db import SessionLocal
from app.crud.users import create_user, validate_charlotte_email, validate_password

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Signup - Campus Market", layout="centered")

# Charlotte colors
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

        /* Inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            background-color: #ffffff !important;
            color: #000000 !important;   /* black typed text */
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
        /* Ensure inner text nodes stay white */
        div.stButton > button *,
        .stFormSubmitButton > button * {
            color: #ffffff !important;
        }
        div.stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background-color: #003d28 !important;
            border-color: #003d28 !important;
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

        /* Force Sign Up button text white */
        div[data-testid="stAppViewContainer"] .stFormSubmitButton > button,
        div[data-testid="stAppViewContainer"] .stFormSubmitButton > button * {
            color: #ffffff !important;
        }

    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Signup")

st.write("Create a new account with your @charlotte.edu email address.")
st.info("Password requirements: At least 8 characters with 1 special character")

# Check if user is already authenticated
if st.session_state.get("authenticated", False):
    st.success(f"✅ You are already logged in as {st.session_state.get('user_email', '')}")
    if st.button("Go to Profile"):
        st.switch_page("pages/4_Profile.py")
    st.stop()

# Show success message if redirected from successful signup
if st.session_state.get("signup_success"):
    st.success("🎉 Signup successful! You are now logged in.")
    st.info("You can now browse listings or create your own!")
    if st.button("Go to Profile"):
        st.switch_page("pages/4_Profile.py")
    st.stop()

with st.form("signup_form"):
    email = st.text_input("Student Email", placeholder="you@charlotte.edu")
    password = st.text_input("Password", type="password", 
                           help="Must be at least 8 characters with 1 special character")
    password_confirm = st.text_input("Confirm Password", type="password")
    submitted = st.form_submit_button("Sign Up")

    if submitted:
        if "form_data" in st.session_state:
            del st.session_state["form_data"]

        if not email.strip():
            st.error("Please enter your student email.")
        else:
            # Validate Charlotte email
            is_valid_email, email_error = validate_charlotte_email(email)
            if not is_valid_email:
                st.error(email_error)
            elif not password:
                st.error("Please enter a password.")
            else:
                # Validate password
                is_valid_password, password_error = validate_password(password)
                if not is_valid_password:
                    st.error(password_error)
                elif password != password_confirm:
                    st.error("Passwords do not match.")
                else:
                    db = SessionLocal()
                    try:
                        user = create_user(db, email.strip().lower(), password)
                        
                        # Start session immediately after signup
                        st.session_state["user_email"] = user.email
                        st.session_state["user_id"] = user.id
                        st.session_state["authenticated"] = True
                        st.session_state["signup_success"] = True
                        
                        st.success("Signup successful! 🎉 You are now logged in. Redirecting to profile.")
                        st.switch_page("pages/4_Profile.py")

                        
                    except ValueError as e:
                        st.error(str(e))
                    finally:
                        db.close()