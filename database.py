import os
import time
from pathlib import Path

from sqlalchemy import Column, Float, String, Text, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db/app.db")

if DATABASE_URL.startswith("sqlite"):
    db_path = Path(DATABASE_URL.replace("sqlite://", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, future=True, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True, expire_on_commit=False)
Base = declarative_base()


def wait_for_db(max_retries: int = 15, delay: float = 2.0):
    """Retry until the database engine can accept a connection."""
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_retries:
                raise
            time.sleep(delay)


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=False)
    ingredients = Column(Text, nullable=False, default="[]")
    instructions = Column(Text, nullable=False)
    substitutions = Column(Text, nullable=False, default="[]")
    tagline = Column(String(255))
    description = Column(Text)
    tags = Column(Text, nullable=False, default="[]")


class PantryItem(Base):
    __tablename__ = "pantry_items"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    quantity = Column(Float)
    unit = Column(String(50))


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
