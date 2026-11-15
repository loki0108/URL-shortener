from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import URL
from app.utils import generate_short_code

MAX_RETRIES = 5


def create_short_url(db: Session, original_url: str) -> URL:
    """Save a new URL with a unique short code.

    If the random code already exists (very rare), the UNIQUE index
    makes the insert fail, so we roll back and try a new code.
    """
    for _ in range(MAX_RETRIES):
        url = URL(short_code=generate_short_code(), original_url=original_url)
        db.add(url)
        try:
            db.commit()
            db.refresh(url)
            return url
        except IntegrityError:
            db.rollback()
    raise RuntimeError("Could not generate a unique short code")


def get_url_by_code(db: Session, short_code: str) -> URL | None:
    """Look up a URL by its short code. Returns None if it doesn't exist."""
    return db.scalar(select(URL).where(URL.short_code == short_code))