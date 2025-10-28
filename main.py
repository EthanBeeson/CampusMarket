import streamlit as st
from app.db import Base, engine, SessionLocal
from app.models.listing import Listing
from app.models.image import Image
from app.crud.listings import create_listing, get_listings, delete_listing, search_listings
from app.crud.listings import mark_listing_sold, ForbiddenAction, update_listing, ALLOWED_CONDITIONS
from app.models.message import Message

# Create database tables
Base.metadata.create_all(bind=engine)

#=============== Streamlit Base Homepage ==================#

# Green background for Charlotte theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #005035; /* UNCC green */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("🏫 Campus Market")
st.write("Welcome to Campus Market! Buy and sell items with UNCC students.")

# Start session
db = SessionLocal()

# --- Sidebar search controls ---
st.sidebar.header("Search & Filters")
search_query = st.sidebar.text_input("Search by keyword")
min_price = st.sidebar.number_input("Min Price", min_value=0.0, step=10.0)
max_price = st.sidebar.number_input("Max Price", min_value=0.0, step=10.0)
# Condition filter in sidebar
conditions = st.sidebar.multiselect(
    "Condition",
    ALLOWED_CONDITIONS,
)

# --- Fetch filtered listings or all listings ---
if search_query or min_price or max_price or conditions:
    listings = search_listings(
        db,
        keyword=search_query if search_query else None,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price > 0 else None,
        conditions=conditions if conditions else None,
    )
else:
    listings = get_listings(db)

# --- Display "No Listings" message if empty ---
if not listings:
    st.markdown(
        """
        <div style="
            background-color:#004830;
            color:#ffffff;
            padding:20px;
            border-radius:12px;
            text-align:center;
            font-size:18px;
            margin-top:20px;
            ">
            <b>No listings found</b><br>
            Try adjusting your search or filters — or check back later for new items!
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # --- Display listings ---
    for l in listings:
        # --- Mark as Sold (Story #7) ---
        # Move this block *inside* the loop and combine the title logic
        is_sold = getattr(l, "is_sold", False)
        label = " 🟡 SOLD" if is_sold else ""
        title_text = f"~~{l.title}~~" if is_sold else l.title

        # Update the header with sold status  (only printed ONCE now)
        st.subheader(f"{title_text} - ${l.price:.2f}{label}")

        # Show condition if available (fallback to 'Unknown' for older rows)
        condition = getattr(l, "condition", "Unknown")
        st.markdown(f"**Condition:** {condition}")
        st.write(l.description)

        # Only show the button to the listing owner
        user_id = st.session_state.get("user_id")
        is_owner = bool(user_id) and (user_id == getattr(l, "user_id", None))

        if is_owner and not is_sold:
            if st.button("Mark as Sold", key=f"sold-{l.id}"):
                try:
                    mark_listing_sold(db, l.id, user_id)
                    st.success("Marked as sold.")
                    st.rerun()
                except ForbiddenAction as e:
                    st.error(str(e))
                except Exception:
                    st.error("Something went wrong marking as sold.")

        
        # --- Edit button + prefilled edit form (Story #75) ---
        if is_owner:
            if st.button("Edit", key=f"edit-{l.id}"):
                st.session_state[f"editing_{l.id}"] = True
                st.rerun()

        # Show edit form if toggled for this listing
        if is_owner and st.session_state.get(f"editing_{l.id}", False):
            st.info("Editing this listing. Update fields and click Save.")
            with st.form(key=f"edit-form-{l.id}", clear_on_submit=False):
                # Prefill with current values
                new_title = st.text_input("Title", value=l.title)
                new_desc = st.text_area("Description", value=l.description or "", height=120)
                new_price = st.number_input("Price", min_value=0.0, value=float(l.price), step=1.0)
                cond_opts = ALLOWED_CONDITIONS
                current_cond = getattr(l, "condition", None) or "Good"
                new_cond = st.selectbox(
                    "Condition",
                    options=cond_opts,
                    index=cond_opts.index(current_cond) if current_cond in cond_opts else 0,
                )

                c_save, c_cancel = st.columns(2)
                save = c_save.form_submit_button("Save")
                cancel = c_cancel.form_submit_button("Cancel")

            # Handle form actions
            if save:
                try:
                    updated = update_listing(
                        db,
                        listing_id=l.id,
                        title=new_title,
                        description=new_desc,
                        price=float(new_price),
                        condition=new_cond,
                    )
                    st.session_state.pop(f"editing_{l.id}", None)
                    st.success("Listing updated.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception:
                    st.error("Something went wrong updating the listing.")
            if cancel:
                st.session_state.pop(f"editing_{l.id}", None)
                st.info("Edit cancelled.")
                st.rerun()

        
          
        # Delete button (with confirmation)  # <-- #79
        if is_owner:
            if st.button("Delete Listing", key=f"delete-{l.id}"):
                st.session_state[f"confirm_del_{l.id}"] = True
                st.rerun()

        # Render confirmation UI if requested (owner only)
        if is_owner and st.session_state.get(f"confirm_del_{l.id}", False):
            st.warning("Are you sure you want to delete this listing? This cannot be undone.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"confirm-yes-{l.id}"):
                deleted = delete_listing(db, listing_id=l.id)
                st.session_state.pop(f"confirm_del_{l.id}", None)
                st.success("Deleted.") if deleted else st.error("Listing not found.")
                st.rerun()
            if c2.button("Cancel", key=f"confirm-no-{l.id}"):
                st.session_state.pop(f"confirm_del_{l.id}", None)
                st.info("Deletion cancelled.")
                st.rerun()

        # (condition filter moved to the sidebar)

        # Show images if any
        if l.images:
            cols = st.columns(len(l.images))
            for col, img in zip(cols, l.images):
                try:
                    col.image(img.url, width=150)
                except FileNotFoundError:
                    col.text("[Image not found]")
        # 💬 Message the Seller Section
        if "user_id" in st.session_state and st.session_state["user_id"] != l.user_id:

            # Small button to toggle message box
            if st.button("💬 Contact Seller", key=f"contact_btn_{l.id}", help="Click to send a message", use_container_width=False):
                st.session_state[f"show_msg_box_{l.id}"] = not st.session_state.get(f"show_msg_box_{l.id}", False)

            # Show message box only if toggled
            if st.session_state.get(f"show_msg_box_{l.id}", False):
                message_text = st.text_area(
                    "Your Message",
                    placeholder="Hi! I'm interested in your listing. Is it still available?",
                    key=f"message_text_{l.id}"
                )

                if st.button("Send Message", key=f"send_message_{l.id}"):
                    if not message_text.strip():
                        st.error("⚠️ Message cannot be empty.")
                    else:
                        db = SessionLocal()
                        try:
                            from app.crud.messages import send_message
                            send_message(
                                db=db,
                                sender_id=st.session_state["user_id"],
                                receiver_id=l.user_id,
                                listing_id=l.id,
                                content=message_text,
                            )
                            st.success("✅ Message sent to seller via in-app messaging!")
                            st.session_state[f"show_msg_box_{l.id}"] = False  # Hide after sending
                        finally:
                            db.close()

        # Separator for next listing
        st.markdown("---")


db.close()
