from sqlalchemy.orm import Session
from app.models.message import Message
from app.models.user import User
from sqlalchemy.orm import joinedload

def send_message(db: Session, sender_id: int, receiver_id: int, content: str, listing_id: int = None):

    # Validate sender
    if not db.query(User).filter(User.id == sender_id).first():
        raise ValueError("Sender does not exist")
    # Validate receiver
    if not db.query(User).filter(User.id == receiver_id).first():
        raise ValueError("Receiver does not exist")
    # Validate content
    if not content.strip():
        raise ValueError("Message content cannot be empty")

    msg = Message(sender_id=sender_id, receiver_id=receiver_id, content=content, listing_id=listing_id)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_user_messages(db: Session, user_id: int):
    return db.query(Message).filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).order_by(Message.created_at.desc()).all()

def mark_as_read(db: Session, message_id: int):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if msg:
        msg.is_read = True
        db.commit()
    return msg

def get_received_messages(db: Session, user_id: int):
    """
    Get all messages received by a user, including sender info.
    """
    return db.query(Message)\
             .options(joinedload(Message.sender))\
             .filter(Message.receiver_id == user_id)\
             .order_by(Message.created_at.desc())\
             .all()
