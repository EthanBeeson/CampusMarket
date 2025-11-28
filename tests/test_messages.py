# tests/test_messages.py
import hashlib
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.user import User
from app.models.listing import Listing
from app.crud.messages import (
    send_message,
    get_user_messages,
    mark_as_read,
    get_received_messages,
)


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def create_user(session, email="user@example.com"):
    hashed_password = hashlib.sha256("password123".encode()).hexdigest()
    user = User(email=email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_listing(session, user_id, title="Test Item", price=10.0):
    listing = Listing(user_id=user_id, title=title, description="A test item", price=price)
    session.add(listing)
    session.commit()
    session.refresh(listing)
    return listing


def test_send_and_receive_message(db_session):
    sender = create_user(db_session, email="sender@example.com")
    receiver = create_user(db_session, email="receiver@example.com")
    listing = create_listing(db_session, user_id=receiver.id, title="Mini Fridge")

    content = "Hi! I'm interested in your listing."
    msg = send_message(db=db_session, sender_id=sender.id, receiver_id=receiver.id, listing_id=listing.id, content=content)
    assert msg.id is not None
    assert msg.content == content

    messages = get_user_messages(db_session, receiver.id)
    assert len(messages) == 1
    retrieved_msg = messages[0]
    assert retrieved_msg.sender_id == sender.id
    assert retrieved_msg.receiver_id == receiver.id
    assert retrieved_msg.listing_id == listing.id

    # Sender should also see the message in their inbox
    sender_messages = get_user_messages(db_session, sender.id)
    assert len(sender_messages) == 1
    assert sender_messages[0].id == msg.id

    # Another user should not see this message
    other_user = create_user(db_session, email="other@example.com")
    other_messages = get_user_messages(db_session, other_user.id)
    assert len(other_messages) == 0


def test_validations_and_mark_read(db_session):
    sender = create_user(db_session, email="sender@example.com")
    receiver = create_user(db_session, email="receiver@example.com")
    listing = create_listing(db_session, user_id=receiver.id, title="Mini Fridge")

    with pytest.raises(ValueError):
        send_message(db=db_session, sender_id=sender.id, receiver_id=9999, listing_id=listing.id, content="Hello")

    with pytest.raises(ValueError):
        send_message(db=db_session, sender_id=9999, receiver_id=receiver.id, listing_id=listing.id, content="Hello")

    with pytest.raises(ValueError):
        send_message(db=db_session, sender_id=sender.id, receiver_id=receiver.id, listing_id=listing.id, content=" ")

    msg = send_message(db=db_session, sender_id=sender.id, receiver_id=receiver.id, listing_id=listing.id, content="Hello")
    assert msg.is_read is False
    updated = mark_as_read(db_session, msg.id)
    assert updated.is_read is True


def test_ordering_and_received_messages(db_session):
    sender = create_user(db_session, email="sender@example.com")
    receiver = create_user(db_session, email="receiver@example.com")

    first = send_message(db_session, sender_id=sender.id, receiver_id=receiver.id, content="first")
    second = send_message(db_session, sender_id=receiver.id, receiver_id=sender.id, content="second")

    # Ensure timestamps are ordered for deterministic sort
    first.created_at = datetime.utcnow() - timedelta(minutes=1)
    second.created_at = datetime.utcnow()
    db_session.commit()

    msgs_for_sender = get_user_messages(db_session, sender.id)
    assert [m.id for m in msgs_for_sender] == [second.id, first.id]

    received = get_received_messages(db_session, receiver.id)
    assert len(received) == 1
    assert received[0].sender.email == sender.email
