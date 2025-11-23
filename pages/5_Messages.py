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
        body, .stApp {
            background-color: #005035 !important;  /* UNCC green background */
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Require login
if "user_id" not in st.session_state:
    st.error("You must be logged in to view messages.")
    st.stop()

USER_ID = st.session_state["user_id"]

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
    st.title(f"💬 Chat with {seller_name}")
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

                st.rerun()

            except Exception as e:
                st.error(str(e))

    db.close()
    st.stop()









# If user has NO messages but clicked "Contact Seller"
# if not all_msgs and forced_other_id: 

    # seller = db.query(User).filter(User.id == forced_other_id).first()
    # listing = db.query(Listing).filter(Listing.id == forced_listing_id).first()

    # seller_name = seller.display_name or seller.full_name or seller.email

   # st.title(f"💬 Start a new chat with {seller_name}")

    # if listing:
        # st.caption(f"About: {listing.title}")

    # st.info("You have no messages yet — start the conversation below")

    # first_message = st.text_area(
        # "Your Message",
        # placeholder="Hi! I'm interested in your listing. Is it still available?",
        # height=120,
        # key="first_message_box"
    # )

    # if st.button("📤 Send first message", use_container_width=True):
        # if not first_message.strip():
            # st.error("Message cannot be empty.")
       #  else:
            # try:
                # send_message(
                    # db=db,
                    # sender_id=USER_ID,
                    # receiver_id=forced_other_id,
                    # listing_id=forced_listing_id,
                    # content=first_message
                # )

                # st.success("✅ Message sent!")

                # Clear the text box
                # st.session_state["first_message_box"] = ""
                
                # Clear these values so it behaves normally next time
                # del st.session_state["open_chat_with_user"]
                # del st.session_state["open_chat_for_listing"]

                # st.session_state["first_message_box"] = ""
                # st.rerun()

            # except Exception as e:
                # st.error(str(e))

    # db.close()
    # st.stop() """ */


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
st.sidebar.header("Your Conversations")

conversation_labels = {}
for (other_id, listing_id), msgs in conversations.items():
    other_user = db.query(User).filter(User.id == other_id).first()
    listing = db.query(Listing).filter(Listing.id == listing_id).first()

    username = get_username(other_user) if other_user else f"User {other_id}"
    listing_title = listing.title if listing else "No Listing"

    label = f"{username} — {listing_title}"
    conversation_labels[label] = (other_id, listing_id)

#selected_label = st.sidebar.selectbox("Select a conversation", list(conversation_labels.keys()))
#selected_other_id, selected_listing_id = conversation_labels[selected_label]

#selected_messages = conversations[(selected_other_id, selected_listing_id)]

#st.sidebar.header("Your Conversations")

# Store selected conversation once user clicks
if "selected_conversation" not in st.session_state:
    st.session_state["selected_conversation"] = None

for label, (other_id, listing_id) in conversation_labels.items():

    if st.sidebar.button(label, use_container_width=True):
        st.session_state["selected_conversation"] = (other_id, listing_id)


# Default to first conversation if none selected yet
if st.session_state["selected_conversation"] is None:
    st.session_state["selected_conversation"] = list(conversation_labels.values())[0]

selected_other_id, selected_listing_id = st.session_state["selected_conversation"]
selected_messages = conversations[(selected_other_id, selected_listing_id)]


#st.title(f"Chat with {selected_label}")

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

# import streamlit as st
# from datetime import datetime
# import sys, os

# # Ensure root folder is searchable
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from app.db import SessionLocal
# from app.crud.messages import (
#     send_message,
#     get_user_messages
# )
# from app.models.user import User
# from app.models.listing import Listing


# st.set_page_config(page_title="Messages", page_icon="💬", layout="wide")

# st.markdown(
#     """
#     <style>
#         body, .stApp {
#             background-color: #005035 !important;  /* UNCC green background */
#         }
#     </style>
#     """,
#     unsafe_allow_html=True
# )


# # Require login
# if "user_id" not in st.session_state:
#     st.error("You must be logged in to view messages.")
#     st.stop()

# USER_ID = st.session_state["user_id"]


# # ------------------------------
# # LOAD ALL MESSAGES
# # ------------------------------
# db = SessionLocal()
# all_msgs = get_user_messages(db, USER_ID)

# if not all_msgs:
#     st.info("You have no messages yet.")
#     st.stop()


# # ------------------------------
# # GROUP MESSAGES BY CONVERSATION
# # Key = (other_user_id, listing_id)
# # ------------------------------
# conversations = {}

# for m in all_msgs:
#     other_id = m.receiver_id if m.sender_id == USER_ID else m.sender_id
#     convo_key = (other_id, m.listing_id)

#     if convo_key not in conversations:
#         conversations[convo_key] = []

#     conversations[convo_key].append(m)


# # ------------------------------
# # SIDEBAR: Conversation List
# # ------------------------------
# st.sidebar.header("Your Conversations")

# conversation_labels = {}
# for (other_id, listing_id), msgs in conversations.items():

#     other_user = db.query(User).filter(User.id == other_id).first()
#     listing = db.query(Listing).filter(Listing.id == listing_id).first()

#     # Build readable username based on your User model
#     def get_username(user):
#         if getattr(user, "display_name", None):
#             return user.display_name
#         if getattr(user, "full_name", None):
#             return user.full_name
#         if getattr(user, "email", None):
#             return user.email
#         return f"User {user.id}"
    
#     conversation_labels = {}
#     for (other_id, listing_id), msgs in conversations.items():

#         other_user = db.query(User).filter(User.id == other_id).first()
#         listing = db.query(Listing).filter(Listing.id == listing_id).first()

#         username = get_username(other_user)
#         listing_title = listing.title if listing else "No Listing"

#         label = f"{username} — {listing_title}"
#         conversation_labels[label] = (other_id, listing_id)

# selected_label = st.sidebar.selectbox("Select a conversation", list(conversation_labels.keys()))
# selected_other_id, selected_listing_id = conversation_labels[selected_label]

# selected_messages = conversations[(selected_other_id, selected_listing_id)]

# st.title(f"Chat with {selected_label}")
# st.markdown("---")


# # ------------------------------
# # DISPLAY MESSAGES
# # ------------------------------
# chat_box = st.container()

# with chat_box:
#     for msg in reversed(selected_messages):  # oldest → newest
#         is_me = msg.sender_id == USER_ID

#         bubble_color = "#DCF8C6" if is_me else "#FFFFFF"
#         align = "flex-end" if is_me else "flex-start"

#         st.markdown(
#             f"""
#             <div style="display:flex; justify-content:{align}; margin:5px 0;">
#                 <div style="
#                     background-color:{bubble_color};
#                     padding:10px 15px;
#                     max-width:60%;
#                     border-radius:12px;
#                     box-shadow:0 1px 2px rgba(0,0,0,0.1);
#                     color: black !important;   /* Force black text */
#                     -webkit-text-fill-color: black
#                 ">
#                     {msg.content}
#                     <div style="font-size:11px; color:gray; text-align:right;">
#                         {msg.created_at.strftime("%Y-%m-%d %H:%M")}
#                     </div>
#                 </div>
#             </div>
#             """,
#             unsafe_allow_html=True
#         )


# st.markdown("---")


# # ------------------------------
# # SEND MESSAGE
# # ------------------------------
# st.subheader("Send a new message")

# new_msg = st.text_area("Your Message", height=80, key="new_msg_box")

# if st.button("Send Message", use_container_width=True):
#     if not new_msg.strip():
#         st.error("Message cannot be empty.")
#     else:
#         try:
#             send_message(
#                 db=db,
#                 sender_id=USER_ID,
#                 receiver_id=selected_other_id,
#                 listing_id=selected_listing_id,
#                 content=new_msg
#             )
#             st.success("Message sent!")
#             st.rerun()
#             st.experimental_rerun()
#         except Exception as e:
#             st.error(f"Error sending message: {str(e)}")

# db.close()
