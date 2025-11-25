from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.favorite import Favorite


def is_favorited(db: Session, user_id: int, listing_id: int) -> bool:
    return (
        db.query(Favorite)
        .filter(
            and_(
                Favorite.user_id == user_id,
                Favorite.listing_id == listing_id,
            )
        )
        .first()
        is not None
    )


def add_favorite(db: Session, user_id: int, listing_id: int):
    favorite = Favorite(user_id=user_id, listing_id=listing_id)
    db.add(favorite)
    db.commit()


def remove_favorite(db: Session, user_id: int, listing_id: int):
    favorite = (
        db.query(Favorite)
        .filter(
            and_(
                Favorite.user_id == user_id,
                Favorite.listing_id == listing_id,
            )
        )
        .first()
    )

    if favorite:
        db.delete(favorite)
        db.commit()


def get_user_favorites(db: Session, user_id: int):
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()
