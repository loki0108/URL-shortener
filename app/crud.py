from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import URL, ClickEvent
from app.utils import generate_short_code

MAX_RETRIES = 5


def create_short_url(db: Session, original_url: str) -> URL:
    """Save a new URL with a unique short code (retries on rare collisions)."""
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


def record_click(
    db: Session, url_id: int, user_agent: str | None, referrer: str | None
) -> None:
    """Increment the click counter and store a click event."""
    # Atomic increment: the database does "clicks = clicks + 1" itself,
    # so two clicks arriving at the same moment are both counted.
    db.execute(update(URL).where(URL.id == url_id).values(clicks=URL.clicks + 1))
    db.add(
        ClickEvent(
            url_id=url_id,
            user_agent=user_agent[:512] if user_agent else None,
            referrer=referrer[:2048] if referrer else None,
        )
    )
    db.commit()


def get_last_click_time(db: Session, url_id: int) -> datetime | None:
    """Return when the link was last clicked, or None if never."""
    return db.scalar(
        select(func.max(ClickEvent.clicked_at)).where(ClickEvent.url_id == url_id)
    )