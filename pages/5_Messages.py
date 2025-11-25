import streamlit as st
from datetime import datetime
import sys, os

# Ensure root folder is searchable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal
from app.crud.messages import send_message, get_user_messages
from app.models.user import User
from app.models.listing import Listing


st.set_page_config(page_title="Messages", page_icon="💬", layout="wide")

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
        /* ADD THIS: Sidebar headers - make them white */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6 {
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

# Require login
if "user_id" not in st.session_state:
    st.error("You must be logged in to view messages.")
    st.stop()

USER_ID = st.session_state["user_id"]

RETURN_TO_MAIN = st.session_state.get("return_to_main_after_send", False)

# ------------------------------
# LOAD ALL MESSAGES
# ------------------------------
db = SessionLocal()
all_msgs = get_user_messages(db, USER_ID)

# Values sent from main page (Contact Seller button)
forced_other_id = st.session_state.get("open_chat_with_user")
forced_listing_id = st.session_state.get("open_chat_for_listing")

# This prevents the "cannot be modified after widget created" error
# ==============================
if "clear_first_message" not in st.session_state:
    st.session_state["clear_first_message"] = False

if st.session_state["clear_first_message"] == True:
    st.session_state["first_message_box"] = ""
    st.session_state["clear_first_message"] = False
# ==============================

# If user clicked "Contact Seller", force this conversation
if forced_other_id and forced_listing_id:

    # Filter messages for this exact conversation
    conversation_msgs = [
        m for m in all_msgs
        if ((m.sender_id == USER_ID and m.receiver_id == forced_other_id) or
            (m.sender_id == forced_other_id and m.receiver_id == USER_ID)) and
           m.listing_id == forced_listing_id
    ]

    seller = db.query(User).filter(User.id == forced_other_id).first()
    listing = db.query(Listing).filter(Listing.id == forced_listing_id).first()

    seller_name = seller.display_name or seller.full_name or seller.email
    st.title(f"Chat with {seller_name}")
    if listing:
        st.caption(f"Listing: {listing.title}")

    if conversation_msgs:
        st.info("Existing conversation:")
        for msg in sorted(conversation_msgs, key=lambda x: x.created_at):
            is_me = msg.sender_id == USER_ID
            align = "flex-end" if is_me else "flex-start"
            bubble_color = "#DCF8C6" if is_me else "#FFFFFF"
            st.markdown(
                f"""
                <div class="chat-row">
                    <div class="chat-bubble {'me' if is_me else 'other'}">
                        {msg.content}
                        <div class="chat-timestamp">
                            {msg.created_at.strftime("%Y-%m-%d %H:%M")}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("You have no messages yet — start the conversation below")

    new_msg = st.text_area(
        "Your Message",
        placeholder="Hi! I'm interested in your listing. Is it still available?",
        height=120,
        key="first_message_box"
    )

    if st.button("📤 Send Message", use_container_width=True):
        if not new_msg.strip():
            st.error("Message cannot be empty.")
        else:
            try:
                send_message(
                    db=db,
                    sender_id=USER_ID,
                    receiver_id=forced_other_id,
                    listing_id=forced_listing_id,
                    content=new_msg.strip()
                )

                st.success("✅ Message sent!")

                # Clear text box
                # st.session_state["first_message_box"] = ""

                st.session_state["clear_first_message"] = True

                # Clear forced chat so normal behavior resumes
                del st.session_state["open_chat_with_user"]
                del st.session_state["open_chat_for_listing"]

                # Redirect back to main page after sending
                st.switch_page("main.py")

                # Redirect back to Main page if coming from Main
                #if RETURN_TO_MAIN:
                    #del st.session_state["return_to_main_after_send"]
                    #st.success("Message sent! Returning to Home Page...")
                    #st.switch_page("main")  # <-- redirects back
                #else:
                    #st.rerun()

            except Exception as e:
                st.error(str(e))

    db.close()
    st.stop()

# ------------------------------
# GROUP MESSAGES BY CONVERSATION
# Key = (other_user_id, listing_id)
# ------------------------------
conversations = {}

for m in all_msgs:
    other_id = m.receiver_id if m.sender_id == USER_ID else m.sender_id
    convo_key = (other_id, m.listing_id)

    if convo_key not in conversations:
        conversations[convo_key] = []

    conversations[convo_key].append(m)

# Helper for displaying username
def get_username(user: User) -> str:
    if getattr(user, "display_name", None):
        return user.display_name
    if getattr(user, "full_name", None):
        return user.full_name
    if getattr(user, "email", None):
        return user.email
    return f"User {user.id}"

# ------------------------------
# SIDEBAR: Conversation List
# ------------------------------
# Sidebar: conversation list
st.sidebar.header("Your Conversations")

conversation_labels = {}

# Build the conversation labels and remember latest message timestamp
for (other_id, listing_id), msgs in conversations.items():
    other_user = db.query(User).filter(User.id == other_id).first()
    listing = db.query(Listing).filter(Listing.id == listing_id).first()

    username = get_username(other_user) if other_user else f"User {other_id}"
    listing_title = listing.title if listing else "No Listing"

    label = f"{username} — {listing_title}"
    conversation_labels[label] = (other_id, listing_id, max(msg.created_at for msg in msgs))

# Sort labels by latest message timestamp descending
sorted_labels = sorted(conversation_labels.items(), key=lambda x: x[1][2], reverse=True)

# Check if the user has any previous conversations
if not sorted_labels:
    st.title("Messages")
    st.info("You have no conversations yet. Start a conversation by clicking 'Contact Seller' on a listing!")
    db.close()
    st.stop()

# Sidebar buttons for each conversation
for label, (other_id, listing_id, _) in sorted_labels:
    if st.sidebar.button(label, key=f"conv_{other_id}_{listing_id}", use_container_width=True):
        st.session_state["selected_conversation"] = (other_id, listing_id)

# ------------------------------
# Default to most recent conversation
# ------------------------------
if "selected_conversation" not in st.session_state:
    most_recent = sorted_labels[0][1]  # (other_id, listing_id, latest_timestamp)
    st.session_state["selected_conversation"] = (most_recent[0], most_recent[1])

selected_other_id, selected_listing_id = st.session_state["selected_conversation"]
selected_messages = sorted(conversations[(selected_other_id, selected_listing_id)], key=lambda m: m.created_at)


#st.sidebar.header("Your Conversations")

#conversation_labels = {}
#for (other_id, listing_id), msgs in conversations.items():
    #other_user = db.query(User).filter(User.id == other_id).first()
    #listing = db.query(Listing).filter(Listing.id == listing_id).first()

    #username = get_username(other_user) if other_user else f"User {other_id}"
    #listing_title = listing.title if listing else "No Listing"

    #label = f"{username} — {listing_title}"
    #conversation_labels[label] = (other_id, listing_id)

#selected_label = st.sidebar.selectbox("Select a conversation", list(conversation_labels.keys())) nounmark
#selected_other_id, selected_listing_id = conversation_labels[selected_label] nounmark

#selected_messages = conversations[(selected_other_id, selected_listing_id)]  nounmark

#st.sidebar.header("Your Conversations")  no unamrk

# Store selected conversation once user clicks
#if "selected_conversation" not in st.session_state:
   # st.session_state["selected_conversation"] = None

#for label, (other_id, listing_id) in conversation_labels.items():

    #if st.sidebar.button(label, use_container_width=True):
        #st.session_state["selected_conversation"] = (other_id, listing_id)


# Default to first conversation if none selected yet
#if st.session_state["selected_conversation"] is None:
    # Direct back to main page if no conversation have been started
    #st.title("Messages")
    #st.info("No conversations have been started yet.")
    #st.markdown("Go to the Home Page and click Contact Seller on a listing to start a conversation!")
    #db.close()
    #st.stop()

#selected_other_id, selected_listing_id = st.session_state["selected_conversation"]
#selected_messages = conversations[(selected_other_id, selected_listing_id)]


#st.title(f"Chat with {selected_label}")   Dont unmark this one

other_user = db.query(User).filter(User.id == selected_other_id).first()
listing = db.query(Listing).filter(Listing.id == selected_listing_id).first()

username = get_username(other_user) if other_user else f"User {selected_other_id}"
listing_title = listing.title if listing else "No Listing"

st.title(f"Chat with {username} — {listing_title}")

st.markdown("---")

# ------------------------------
# DISPLAY MESSAGES
# ------------------------------
chat_box = st.container()

# Optional: ensure messages sorted by time
selected_messages = sorted(selected_messages, key=lambda m: m.created_at)

with chat_box:
    for msg in selected_messages:  # oldest → newest
        is_me = msg.sender_id == USER_ID

        bubble_color = "#DCF8C6" if is_me else "#FFFFFF"
        align = "flex-end" if is_me else "flex-start"

        st.markdown(
            f"""
            <div style="display:flex; justify-content:{align}; margin:5px 0;">
                <div style="
                    background-color:{bubble_color};
                    padding:10px 15px;
                    max-width:60%;
                    border-radius:12px;
                    box-shadow:0 1px 2px rgba(0,0,0,0.1);
                    color: black !important;
                    -webkit-text-fill-color: black;
                ">
                    {msg.content}
                    <div style="font-size:11px; color:gray; text-align:right;">
                        {msg.created_at.strftime("%Y-%m-%d %H:%M")}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("---")

# ------------------------------
# SEND MESSAGE
# ------------------------------
st.subheader("Send a new message")

if "clear_msg" not in st.session_state:
    st.session_state["clear_msg"] = False

if st.session_state["clear_msg"] == True:
    st.session_state["new_msg_box"] = ""
    st.session_state["clear_msg"] = False

new_msg = st.text_area(
    "Your Message",
    height=80,
    key="new_msg_box"
)

if st.button("Send Message", use_container_width=True):
    if not new_msg.strip():
        st.error("Message cannot be empty.")
    else:
        try:
            send_message(
                db=db,
                sender_id=USER_ID,
                receiver_id=selected_other_id,
                listing_id=selected_listing_id,
                content=new_msg.strip()
            )

            st.success("Message sent!")

            # CLEAR the text box
            st.session_state["clear_msg"] = True

            st.rerun()

        except Exception as e:
            st.error(f"Error sending message: {str(e)}")

db.close()
