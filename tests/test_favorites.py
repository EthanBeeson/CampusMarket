import pytest
from unittest.mock import MagicMock
import main

# --- Mock listing object ---
class MockListing:
    def __init__(self, id, user_id):
        self.id = id
        self.user_id = user_id

# --- Minimal render_listing function for testing favorites ---
def render_listing_for_test(l):
    db = main.db
    user_id = main.st.session_state.get("user_id")
    if user_id and l.user_id != user_id:
        favorited = main.is_favorited(db, user_id, l.id)
        if favorited:
            main.remove_favorite(db, user_id, l.id)
        else:
            main.add_favorite(db, user_id, l.id)
    db.close()

# --- Fixtures ---
@pytest.fixture
def mock_st(monkeypatch):
    monkeypatch.setattr(main, "st", MagicMock())
    main.st.session_state = {"user_id": 1}
    return main.st

@pytest.fixture
def mock_db():
    return main.db

# --- Tests ---
def test_favorite_add_remove(mock_db, mock_st):
    listing = MockListing(id=123, user_id=2)

    # Ensure not favorited initially
    assert not main.is_favorited(mock_db, mock_st.session_state["user_id"], listing.id)

    # Add favorite
    main.add_favorite(mock_db, mock_st.session_state["user_id"], listing.id)
    assert main.is_favorited(mock_db, mock_st.session_state["user_id"], listing.id)

    # Remove favorite
    main.remove_favorite(mock_db, mock_st.session_state["user_id"], listing.id)
    assert not main.is_favorited(mock_db, mock_st.session_state["user_id"], listing.id)

def test_render_listing_favorites(mock_db, mock_st):
    listing = MockListing(id=456, user_id=2)

    # Use our minimal test render_listing function
    render_listing_for_test(listing)

    # Should now be favorited
    assert main.is_favorited(mock_db, mock_st.session_state["user_id"], listing.id)

    # Run again to remove favorite
    render_listing_for_test(listing)
    assert not main.is_favorited(mock_db, mock_st.session_state["user_id"], listing.id)

