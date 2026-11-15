from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models  # noqa: F401  (models import registers tables)
from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.schemas import URLCreate, URLResponse, URLStats


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="URL Shortener",
    description="A scalable URL shortening service built with FastAPI, PostgreSQL and Redis",
    version="0.4.0",
    lifespan=lifespan,
)


def track_click(url_id: int, user_agent: str | None, referrer: str | None) -> None:
    """Background task: runs after the redirect is sent, with its own DB session."""
    db = SessionLocal()
    try:
        crud.record_click(db, url_id, user_agent, referrer)
    finally:
        db.close()


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Confirms the service is running and can reach the database."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "connected"}


@app.get("/", include_in_schema=False)
def root():
    """Send visitors of the bare address to the API docs."""
    return RedirectResponse(url="/docs")


@app.post("/shorten", response_model=URLResponse, status_code=201)
def shorten_url(payload: URLCreate, db: Session = Depends(get_db)):
    """Create a short link for the given long URL."""
    url = crud.create_short_url(db, str(payload.url))
    return URLResponse(
        short_code=url.short_code,
        short_url=f"{settings.base_url}/{url.short_code}",
        original_url=url.original_url,
    )


@app.get("/stats/{short_code}", response_model=URLStats)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    """Return click statistics for a short link."""
    url = crud.get_url_by_code(db, short_code)
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return URLStats(
        short_code=url.short_code,
        original_url=url.original_url,
        clicks=url.clicks,
        created_at=url.created_at,
        last_clicked_at=crud.get_last_click_time(db, url.id),
    )


# Keep this route LAST: "/{short_code}" matches any single path segment.
@app.get("/{short_code}")
def redirect_to_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Redirect to the original URL and record the click in the background."""
    url = crud.get_url_by_code(db, short_code)
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    background_tasks.add_task(
        track_click,
        url.id,
        request.headers.get("user-agent"),
        request.headers.get("referer"),
    )
    return RedirectResponse(url=url.original_url, status_code=302)