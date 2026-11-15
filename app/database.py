from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# pool_pre_ping checks a connection is alive before using it
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class that all database models inherit from."""
    pass


def get_db():
    """FastAPI dependency: opens a DB session per request and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()