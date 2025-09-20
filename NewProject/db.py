import os
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

DB_URL = os.getenv("DB_URL", "sqlite:///ayush_lookup.db")

def _make_engine(url: str):
    kwargs = dict(future=True, echo=False, pool_pre_ping=True)
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)

engine = _make_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)

    lookups = relationship("LookupLog", back_populates="user")


class LookupLog(Base):
    __tablename__ = "lookup_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    disease_text = Column(String, nullable=False)
    result_json = Column(JSON, nullable=False)  # stored as JSON in SQLite
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="lookups")

def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print(f"Initialized DB at {DB_URL}")
