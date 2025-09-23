from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

# Base class for all models
ORMBase = declarative_base()

# Example User model
class User(ORMBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
