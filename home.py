import streamlit as st
from PIL import Image
import os
import base64
from app.db import Base, engine, SessionLocal
from app.nav import render_nav_sidebar
from app.models.listing import Listing
from app.models.image import Image as ImageModel
from app.crud.listings import (
    create_listing, get_listings, delete_listing, search_listings,
    mark_listing_sold, ForbiddenAction, update_listing, ALLOWED_CONDITIONS
)
from app.crud.listings import ALLOWED_CATEGORIES
from app.models.message import Message
from app.models.user import User
from app.crud.reviews import get_reviews_for_user, get_user_average_rating
from app.crud.favorites import is_favorited, add_favorite, remove_favorite


st.set_page_config(page_title="Campus Market", layout="wide")

# Custom navigation sidebar (replaces default multipage nav)
render_nav_sidebar()


# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure 'category' column exists in SQLite DB
from sqlalchemy import text
with engine.begin() as conn:
    try:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(listings);"))]
        if "category" not in cols:
            # Add column with default 'Other' for existing rows
            conn.execute(text("ALTER TABLE listings ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'Other';"))
    except Exception:
        pass

# ======= Global Styles (center content, tidy buttons, subtle card) ======= #
st.markdown(
    """
    <style>
      /* CHANGED: White background instead of green */
      .stApp { background-color: #fffdf2; }
      
      /* center column width */
      .block-container { max-width: 900px; margin: 0 auto; }
      
      /* UPDATED: Listing card with white background and green border */
      .card {
        background: #ffffff;
        border: 2px solid #005035;  /* CHANGED: Charlotte green border */
        border-radius: 14px;
        padding: 18px 20px;
        margin: 18px 0 26px 0;
        box-shadow: 0 4px 12px rgba(0, 80, 53, 0.1);  /* ADDED: Subtle shadow */
      }
      
      /* center headings inside cards without changing global titles */
      .card h2, .card h3, .card p { margin: 6px 0; }
      .center { text-align: center; }
      
      /* UPDATED: Nicer buttons with Charlotte green */
      div.stButton > button {
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
        border: 2px solid #005035;  /* CHANGED: Green border */
        background-color: #005035;   /* CHANGED: Green background */
        color: white;                /* CHANGED: White text */
      }
      
      /* UPDATED: Hover effect for buttons */
      div.stButton > button:hover {
        background-color: #003d28;   /* CHANGED: Darker green on hover */
        border-color: #003d28;
      }

      /* Focused / active multiselect/select wrappers */
      [data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"][data-focus="true"] > div,
      .block-container .stMultiSelect div[data-baseweb="select"][data-focus="true"] > div,
      
      /* compact vertical spacing between stacked widgets */
      .element-container:has(> div.stButton) { margin: 0.2rem 0; }
      
      /* carousel nav buttons */
      .navbtn > button { width: 100%; }

      /* UPDATED: Category buttons with Charlotte green */
      .stSidebar [data-baseweb="tag"] {
          background-color: #005035 !important;   /* Charlotte green */
          color: white !important;
       }

    /* Remove border color entirely from select widgets — scoped to main page */
    .main-page section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    .main-page .block-container div[data-baseweb="select"] > div,
    .main-page div[data-baseweb="select"] > div,
    .main-page div[data-baseweb="select"][data-focus="true"] > div,
    .main-page div[data-baseweb="select"][aria-expanded="true"] > div,
    .main-page div[data-baseweb="select"]:focus-within > div,
    .main-page .stSelectbox > div {
        border: none !important;
        box-shadow: none !important;
    }

    /* Remove any visible border/outline when sidebar inputs are focused */
    section[data-testid="stSidebar"] input[type="text"]:focus,
    section[data-testid="stSidebar"] input[type="search"]:focus,
    section[data-testid="stSidebar"] input[type="number"]:focus,
    section[data-testid="stSidebar"] textarea:focus,
    section[data-testid="stSidebar"] .stTextInput:focus-within > div > div,
    section[data-testid="stSidebar"] .stNumberInput:focus-within > div > div,
    section[data-testid="stSidebar"] .stTextArea:focus-within > div > div {
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* Also ensure focused inputs don't get an outline color from Streamlit */
    section[data-testid="stSidebar"] input:focus,
    section[data-testid="stSidebar"] textarea:focus {
        outline-color: transparent !important;
    }

    /* Strong global override: remove any focus/border/box-shadow for elements inside the sidebar */
    section[data-testid="stSidebar"] *:focus,
    section[data-testid="stSidebar"] *:focus-visible,
    section[data-testid="stSidebar"] *:focus-within {
        outline: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* UPDATED: Owner info section with green accents */
    .owner-section {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px;
      border-radius: 8px;
      cursor: pointer;
      transition: background-color 0.2s ease;
      margin-bottom: 12px;
      background: rgba(0, 80, 53, 0.05);  /* CHANGED: Light green background */
      border: 1px solid rgba(0, 80, 53, 0.1);  /* ADDED: Subtle green border */
    }
    
    .owner-section:hover {
      background: rgba(0, 80, 53, 0.1);  /* CHANGED: Darker green on hover */
    }
    
    .owner-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid #005035;  /* CHANGED: Green border */
    }
    
    .owner-avatar-placeholder {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #005035;  /* CHANGED: Charlotte green */
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      border: 2px solid #005035;
    }
    
    .owner-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    
    .owner-name {
      font-weight: 600;
      color: #005035;  /* CHANGED: Green text */
      font-size: 0.95em;
    }
    
    .owner-rating {
      font-size: 0.85em;
      color: #666666;  /* CHANGED: Dark gray for better contrast */
    }
    
    /* NEW: Improved search bar styling */
    .search-container {
      text-align: center;
      margin: 80px auto 50px auto;
      max-width: 700px;
      padding: 40px;
      background: white;
      border-radius: 20px;
      box-shadow: 0 8px 32px rgba(0, 80, 53, 0.1);  /* ADDED: Soft green shadow */
    }
    
    .search-title {
      color: #005035;  /* CHANGED: Green title */
      font-size: 3em;
      margin-bottom: 20px;
      font-weight: bold;
    }

    .title{
        color: #005035;
        font-size: 3em;
        margin-bottom: 20px;
        font-weight: bold;
    }
    
    .search-subtitle {
      color: #666666;  /* CHANGED: Dark gray subtitle */
      font-size: 1.3em;
      margin-bottom: 40px;
    }
    
    /* NEW: Custom search input styling */
    .custom-search-input {
      border: 2px solid #005035 !important;
      border-radius: 50px !important;
      padding: 15px 25px !important;
      font-size: 1.1em !important;
      background: white !important;
    }
    
    .custom-search-input:focus {
      border-color: #003d28 !important;
      box-shadow: 0 0 0 3px rgba(0, 80, 53, 0.1) !important;
    }
    
    /* UPDATED: Text colors for better contrast on white background */
    .stTitle, h1 {
      color: #005035 !important;  /* CHANGED: Green titles */
    }
    
    .stMarkdown {
      color: #333333 !important;  /* CHANGED: Dark text for better readability */
    }
    
    /* UPDATED: Sold label color */
    .sold-label {
      color: #d32f2f !important;  /* CHANGED: Red for sold items */
      font-weight: bold;
    }
    .listings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 20px; /* space between cards */
        }

    .card {
        background: #ffffff;
        border: 2px solid #005035;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 8px 32px rgba(0, 80, 53, 0.1); /* glowing effect */
        transition: all 0.2s ease;
    }

    .card:hover {
        box-shadow: 0 12px 36px rgba(0, 80, 53, 0.2);
        transform: translateY(-2px); /* subtle lift on hover */
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)
# Start session
db = SessionLocal()

# --- Sidebar search controls ---
st.sidebar.header("Advanced Search")
search_query = st.sidebar.text_input("Search by keyword", placeholder="e.g. textbook, laptop")

# Use text_input with placeholder instead of number_input
min_price_str = st.sidebar.text_input("Min Price", placeholder="-")
max_price_str = st.sidebar.text_input("Max Price", placeholder="-")

# Convert to floats only if user entered something
def parse_price(value):
    try:
        return float(value) if value.strip() != "" else None
    except ValueError:
        return None

min_price = parse_price(min_price_str)
max_price = parse_price(max_price_str)
# Default to 0.00 and +inf if not provided
min_price = min_price if min_price is not None else float("0")
max_price = max_price if max_price is not None else float("inf")

conditions = st.sidebar.multiselect("Condition", ALLOWED_CONDITIONS)
categories = st.sidebar.multiselect("Category", ALLOWED_CATEGORIES)

# Use get() method to safely access session state
search_initiated = st.session_state.get('search_initiated', False)

# Main search bar in center of page
if not search_initiated:
    st.markdown(
        """
        <div class="search-container">
          <div class="search-title">Campus Market</div>
          <div class="search-subtitle">What are you looking for today?</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Center the search bar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        main_search_query = st.text_input(
            "Search for items...",
            placeholder="Type what you're looking for and press Enter...",
            label_visibility="collapsed",
            key="main_search_input"
        )
        
        search_button = st.button("Search Campus Market", use_container_width=True, key="main_search_button")
        
        if main_search_query.strip() or search_button:
            st.session_state.search_initiated = True
            st.session_state.main_search_query = main_search_query
            st.rerun()
else:
    # Display the main title when search is initiated
    st.title("Campus Market")
    # Add clear search button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Clear Search", type="secondary"):
            st.session_state.search_initiated = False
            st.session_state.main_search_query = ''
            st.rerun()
    
    main_search_query = st.session_state.get('main_search_query', '')
    if main_search_query:
        st.write(f"Showing results for: **{main_search_query}**")
    else:
        st.write("Browse all listings below:")

# --- Combine both search methods ---
# Determine which search query to use (main search takes priority)
main_search_query = st.session_state.get('main_search_query', '')
active_search_query = main_search_query if main_search_query else search_query

# --- Fetch filtered listings ---
# Use search_listings if ANY search criteria are present
has_search_criteria = (
    active_search_query or 
    min_price > 0 or 
    max_price != float('inf') or 
    conditions or 
    categories
)

if has_search_criteria:
    listings = search_listings(
        db,
        keyword=active_search_query if active_search_query else None,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price > 0 else None,
        conditions=conditions if conditions else None,
        categories=categories if categories else None,
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
        from app.db import SessionLocal #added for favs
        db = SessionLocal() #added for favs
        is_sold = getattr(l, "is_sold", False)
        label = " 🟡 SOLD" if is_sold else ""
        title_text = f"~~{l.title}~~" if is_sold else l.title
        st.markdown("---")
        # --- Owner section (clickable to view public profile) ---
        owner = db.query(User).filter(User.id == l.user_id).first()

        # --- Favorite button ---
        if "user_id" in st.session_state:
            current_user_id = st.session_state["user_id"]

            # Only show favorite button if the user is NOT the owner
            if l.user_id != current_user_id:
                favorited = is_favorited(db, current_user_id, l.id)

                # Set heart label: white if not favorited, red if favorited
                heart_label = "❤️" if favorited else "🤍"

                if st.button(heart_label, key=f"fav_{l.id}", use_container_width=True):
                    if favorited:
                        remove_favorite(db, current_user_id, l.id)
                    else:
                        add_favorite(db, current_user_id, l.id)
                    st.rerun()

        # Only show favorite button if user is logged in
        #if "user_id" in st.session_state and st.session_state["user_id"] is not None:

            #current_user_id = st.session_state["user_id"]
            #if l.user_id != current_user_id:  # <-- Skip own listings
                #favorited = is_favorited(db, st.session_state["user_id"], l.id)

                #if favorited:
                    #if st.button("🤍", key=f"fav_{l.id}"):
                        #remove_favorite(db, st.session_state["user_id"], l.id)
                        #st.rerun()
                #else:
                    #if st.button("❤️", key=f"fav_{l.id}"):
                        #add_favorite(db, st.session_state["user_id"], l.id)
                        #st.rerun()

        else:
            st.caption("Log in to save this listing")

        db.close()


        # Always render owner container; use fallbacks when user or profile picture missing
        owner_exists = bool(owner)
        owner_display_name = (owner.full_name or owner.display_name) if owner_exists else None
        owner_display_name = owner_display_name or f"User {getattr(l, 'user_id', 'Unknown')}"

        rating_text = "No ratings"
        if owner_exists:
            avg_rating = get_user_average_rating(db, owner.id)
            rating_text = f"⭐ {avg_rating:.1f}" if avg_rating else "No ratings"

        # Resolve profile picture if available
        profile_pic_path = None
        if owner_exists and owner.profile_picture:
            candidates = [
                owner.profile_picture,
                os.path.join(os.getcwd(), owner.profile_picture),
                os.path.join(os.getcwd(), "uploads", "profile_pictures", owner.profile_picture),
            ]
            for p in candidates:
                try:
                    if p and os.path.exists(p):
                        profile_pic_path = p
                        break
                except Exception:
                    continue

        # Build owner HTML block
        owner_parts = []
        owner_parts.append(f'<div class="owner-section" style="display:flex;align-items:center;gap:10px;">')

        if profile_pic_path:
            try:
                with open(profile_pic_path, "rb") as f:
                    img_data = f.read()
                b64 = base64.b64encode(img_data).decode()
                mime = "image/jpeg" if profile_pic_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                owner_parts.append(f'<img class="owner-avatar" src="data:{mime};base64,{b64}" alt="{owner_display_name}">')
            except Exception:
                owner_parts.append(f'<div class="owner-avatar-placeholder">{owner_display_name[0].upper()}</div>')
        else:
            owner_parts.append(f'<div class="owner-avatar-placeholder">{owner_display_name[0].upper()}</div>')

        owner_parts.append(f'<div class="owner-info"><div class="owner-name">{owner_display_name}</div><div class="owner-rating">{rating_text}</div></div>')
        owner_parts.append('</div>')

        # Render owner block with "Open Profile" button
        col_left, col_right = st.columns([0.70, 0.30])
        with col_left:
            # Render owner HTML block (avatar + name + rating)
            st.markdown("".join(owner_parts), unsafe_allow_html=True)
        with col_right:
            # Button to open the dedicated public profile page (same-tab)
            if owner_exists:
                if st.button("Open Profile", key=f"open_page_{getattr(l,'user_id','unknown')}_{l.id}"):
                    st.session_state['public_profile_user_id'] = owner.id
                    try:
                        st.query_params["user_id"] = str(owner.id)
                    except Exception:
                        # fallback to older API name
                        try:
                            st.experimental_set_query_params(user_id=str(owner.id))
                        except Exception:
                            pass
                    st.switch_page("pages/Public_Profile.py")


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
                # Category selector in edit form
                cat_opts = ALLOWED_CATEGORIES
                current_cat = getattr(l, "category", None) or "Other"
                new_cat = st.selectbox(
                    "Category",
                    options=cat_opts,
                    index=cat_opts.index(current_cat) if current_cat in cat_opts else 0,
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
                        category=new_cat,
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
                    if st.button("->", key=f"next_{l.id}", use_container_width=True):
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
            
            contact_key = f"contact_btn_{l.id}"


            if st.button(
                "💬 Contact Seller",
                key=f"contact_btn_{l.id}",
                help="Click to send a message",
                use_container_width=True
            ):

                # Save info for Messages page
                st.session_state["open_chat_with_user"] = l.user_id
                st.session_state["open_chat_for_listing"] = l.id

                # Redirect to Messages tab
                st.switch_page("pages/5_Messages.py")

        st.markdown('</div>', unsafe_allow_html=True)  # end card

        # FAVORITE BUTTON (heart)
        #if "user_id" in st.session_state and st.session_state["user_id"] is not None:

            #db = SessionLocal()
            #favorited = is_favorited(db, st.session_state["user_id"], l.id)

            #heart = "❤️" if favorited else "🤍"
            #unique_key = f"fav_{l.id}_{hash(str(l.title))}"

            #if st.button(heart, key=unique_key):
                #if favorited:
                    #remove_favorite(db, st.session_state["user_id"], l.id)
                #else:
                    #add_favorite(db, st.session_state["user_id"], l.id)

                #db.close()
               # st.rerun()

            #db.close()

    # Render all listings
    for item in listings:
            render_listing(item)

db.close()
