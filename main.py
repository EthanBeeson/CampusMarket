import streamlit as st
from PIL import Image
from app.db import Base, engine, SessionLocal
from app.models.listing import Listing
from app.models.image import Image as ImageModel
from app.crud.listings import (
    create_listing, get_listings, delete_listing, search_listings,
    mark_listing_sold, ForbiddenAction, update_listing, ALLOWED_CONDITIONS
)
from app.models.message import Message

st.set_page_config(page_title="Campus Market", layout="wide")

# Create database tables
Base.metadata.create_all(bind=engine)

# ======= Global Styles (center content, tidy buttons, subtle card) ======= #
st.markdown(
    """
    <style>
      .stApp { background-color: #005035; }
      /* center column width */
      .block-container { max-width: 900px; margin: 0 auto; }
      /* listing card */
      .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 18px 20px;
        margin: 18px 0 26px 0;
      }
      /* center headings inside cards without changing global titles */
      .card h2, .card h3, .card p { margin: 6px 0; }
      .center { text-align: center; }
      /* nicer buttons */
      div.stButton > button {
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
        border: 1px solid rgba(255,255,255,0.15);
      }
      /* compact vertical spacing between stacked widgets */
      .element-container:has(> div.stButton) { margin: 0.2rem 0; }
      /* carousel nav buttons */
      .navbtn > button { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
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
conditions = st.sidebar.multiselect("Condition", ALLOWED_CONDITIONS)

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
        <div class="card center" style="background: rgba(0,0,0,0.15);">
          <b>No listings found</b><br>
          Try adjusting your search or filters — or check back later for new items!
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # ---------- Listing Renderer ---------- #
    def render_listing(l):
        is_sold = getattr(l, "is_sold", False)
        label = " 🟡 SOLD" if is_sold else ""
        title_text = f"~~{l.title}~~" if is_sold else l.title

        st.markdown('<div class="card">', unsafe_allow_html=True)

        # Title centered
        st.markdown(
            f"<h2 class='center'>{title_text} - ${float(l.price):.2f}{label}</h2>",
            unsafe_allow_html=True,
        )

        # Meta + description centered
        condition = getattr(l, "condition", "Unknown")
        st.markdown(f"<p class='center'><b>Condition:</b> {condition}</p>", unsafe_allow_html=True)
        if l.description:
            st.markdown(f"<p class='center'>{l.description}</p>", unsafe_allow_html=True)

        # Owner actions (centered row)
        user_id = st.session_state.get("user_id")
        is_owner = bool(user_id) and (user_id == getattr(l, "user_id", None))

        if is_owner:
            a1, a2, a3 = st.columns(3)
            with a1:
                if not is_sold:
                    if st.button("Mark as Sold", key=f"sold-{l.id}", use_container_width=True):
                        try:
                            mark_listing_sold(db, l.id, user_id)
                            st.success("Marked as sold.")
                            st.rerun()
                        except ForbiddenAction as e:
                            st.error(str(e))
                        except Exception:
                            st.error("Something went wrong marking as sold.")
                else:
                    st.button("Marked Sold", key=f"sold-disabled-{l.id}", disabled=True, use_container_width=True)

            with a2:
                if st.button("Edit", key=f"edit-{l.id}", use_container_width=True):
                    st.session_state[f"editing_{l.id}"] = True
                    st.rerun()

            with a3:
                if st.button("Delete Listing", key=f"delete-{l.id}", use_container_width=True):
                    st.session_state[f"confirm_del_{l.id}"] = True
                    st.rerun()

        # Edit form (centered under actions)
        if is_owner and st.session_state.get(f"editing_{l.id}", False):
            st.info("Editing this listing. Update fields and click Save.")
            with st.form(key=f"edit-form-{l.id}", clear_on_submit=False):
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

            if save:
                try:
                    update_listing(
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

        # Delete confirm
        if is_owner and st.session_state.get(f"confirm_del_{l.id}", False):
            st.warning("Are you sure you want to delete this listing? This cannot be undone.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"confirm-yes-{l.id}", use_container_width=True):
                deleted = delete_listing(db, listing_id=l.id)
                st.session_state.pop(f"confirm_del_{l.id}", None)
                st.success("Deleted.") if deleted else st.error("Listing not found.")
                st.rerun()
            if c2.button("Cancel", key=f"confirm-no-{l.id}", use_container_width=True):
                st.session_state.pop(f"confirm_del_{l.id}", None)
                st.info("Deletion cancelled.")
                st.rerun()

        # ----- Centered Image Carousel (single NEXT button) -----
        if l.images:
            # per-listing index
            key_idx = f"img_idx_{l.id}"
            if key_idx not in st.session_state:
                st.session_state[key_idx] = 0

            img_idx = st.session_state[key_idx]
            total = len(l.images)
            try:
                img_path = l.images[img_idx].url
                img = Image.open(img_path).convert("RGB")
            except FileNotFoundError:
                img = None
                st.warning("[Image not found]")
            except Exception as e:
                img = None
                st.error(f"Error displaying image: {e}")

            # center the image in a fixed middle column
            L, M, R = st.columns([1, 2, 1])
            with M:
                if img is not None:
                    st.image(img, use_container_width=True)

                # SINGLE centered button to advance
                bL, bC, bR = st.columns([2, 1, 2])
                with bC:
                    if st.button("Next ▸", key=f"next_{l.id}", use_container_width=True):
                        st.session_state[key_idx] = (img_idx + 1) % total
                        st.rerun()

            st.markdown(
                f"<p class='center' style='color:rgba(255,255,255,0.6)'>Image {img_idx + 1} of {total}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<p class='center' style='opacity:.8'>No images available for this listing.</p>", unsafe_allow_html=True)

        # Message seller for non-owner
        if "user_id" in st.session_state and st.session_state["user_id"] != getattr(l, "user_id", None):
            if st.button("💬 Contact Seller", key=f"contact_btn_{l.id}", help="Click to send a message", use_container_width=True):
                st.session_state[f"show_msg_box_{l.id}"] = not st.session_state.get(f"show_msg_box_{l.id}", False)

            if st.session_state.get(f"show_msg_box_{l.id}", False):
                message_text = st.text_area(
                    "Your Message",
                    placeholder="Hi! I'm interested in your listing. Is it still available?",
                    key=f"message_text_{l.id}"
                )
                if st.button("Send Message", key=f"send_message_{l.id}", use_container_width=True):
                    if not message_text.strip():
                        st.error("⚠️ Message cannot be empty.")
                    else:
                        db2 = SessionLocal()
                        try:
                            from app.crud.messages import send_message
                            send_message(
                                db=db2,
                                sender_id=st.session_state["user_id"],
                                receiver_id=l.user_id,
                                listing_id=l.id,
                                content=message_text,
                            )
                            st.success("✅ Message sent to seller!")
                            st.session_state[f"show_msg_box_{l.id}"] = False
                        finally:
                            db2.close()

        st.markdown('</div>', unsafe_allow_html=True)  # end card

    # Render all listings
    for item in listings:
        render_listing(item)

db.close()
