import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Allow override, but default to a shared, pre-seeded database file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./campus_market_global.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

Base.metadata.create_all(bind=engine)

# IMPORTANT: Import models so tables get created
from app.models.favorite import Favorite
