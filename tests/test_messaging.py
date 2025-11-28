import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import importlib.util
import sys
from pathlib import Path

# --------------------------------------
# MOCK STREAMLIT BEFORE IMPORTING 5_Messages.py
# --------------------------------------

mock_st = MagicMock()
mock_st.session_state = {"user_id": 1}

# All commonly used attributes/methods in 5_Messages.py
mock_st.set_page_config = MagicMock()
mock_st.markdown = MagicMock()
mock_st.error = MagicMock()
mock_st.stop = MagicMock()
mock_st.title = MagicMock()
mock_st.caption = MagicMock()
mock_st.info = MagicMock()
mock_st.text_area = MagicMock(return_value="Hello test message")
mock_st.button = MagicMock(return_value=True)
mock_st.success = MagicMock()
mock_st.rerun = MagicMock()
mock_st.sidebar = MagicMock()
mock_st.container = MagicMock(return_value=MagicMock())

sys.modules["streamlit"] = mock_st

# --------------------------------------
# AUTO-FIND 5_Messages.py
# --------------------------------------

root = Path(__file__).parents[1]
matches = list(root.rglob("5_Messages.py"))

if not matches:
    raise FileNotFoundError("❌ Could not find 5_Messages.py anywhere in the project")

messages_path = matches[0]

spec = importlib.util.spec_from_file_location("messages", messages_path)
messages = importlib.util.module_from_spec(spec)
sys.modules["messages"] = messages
spec.loader.exec_module(messages)

get_username = messages.get_username
render_messages = messages.render_messages


# --------------------------------------
# MOCK MESSAGE OBJECT
# --------------------------------------

class MockMessage:
    def __init__(self, sender_id, receiver_id, content, created_at=None, listing_id=1):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.created_at = created_at or datetime.now()
        self.listing_id = listing_id


# --------------------------------------
# TEST: get_username
# --------------------------------------

def test_get_username_display_name():
    user = SimpleNamespace(
        id=1,
        display_name="Sanjana",
        full_name="Sanjana Pogula",
        email="sanjana@email.com"
    )
    assert get_username(user) == "Sanjana"


def test_get_username_full_name():
    user = SimpleNamespace(
        id=2,
        display_name=None,
        full_name="Alex Johnson",
        email="alex@email.com"
    )
    assert get_username(user) == "Alex Johnson"


def test_get_username_email():
    user = SimpleNamespace(
        id=3,
        display_name=None,
        full_name=None,
        email="test@email.com"
    )
    assert get_username(user) == "test@email.com"


def test_get_username_fallback():
    user = SimpleNamespace(
        id=99,
        display_name=None,
        full_name=None,
        email=None
    )
    assert get_username(user) == "User 99"


# --------------------------------------
# TEST: render_messages
# --------------------------------------

@patch("messages.st.markdown")
def test_render_messages_orders_and_renders(mock_markdown):
    messages_list = [
        MockMessage(2, 1, "Hello", datetime(2024, 1, 2, 9, 0)),
        MockMessage(1, 2, "Hi there", datetime(2024, 1, 2, 10, 0)),
    ]
    render_messages(messages_list, current_user_id=1)

    # Should render twice
    assert mock_markdown.call_count == 2

    first_html = mock_markdown.call_args_list[0][0][0]
    second_html = mock_markdown.call_args_list[1][0][0]

    assert "Hello" in first_html
    assert "Hi there" in second_html


# --------------------------------------
# TEST: Conversation grouping logic
# --------------------------------------

def test_conversation_grouping():
    USER_ID = 1
    messages_list = [
        MockMessage(1, 2, "A", listing_id=10),
        MockMessage(2, 1, "B", listing_id=10),
        MockMessage(1, 3, "C", listing_id=20),
    ]

    conversations = {}

    for m in messages_list:
        other_id = m.receiver_id if m.sender_id == USER_ID else m.sender_id
        convo_key = (other_id, m.listing_id)

        if convo_key not in conversations:
            conversations[convo_key] = []

        conversations[convo_key].append(m)

    assert (2, 10) in conversations
    assert (3, 20) in conversations
    assert len(conversations[(2, 10)]) == 2
    assert len(conversations[(3, 20)]) == 1




