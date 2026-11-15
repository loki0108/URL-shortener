from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models  # noqa: F401  (models import registers tables)
from app.config import settings
from app.database import Base, engine, get_db
from app.schemas import URLCreate, URLResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="URL Shortener",
    description="A scalable URL shortening service built with FastAPI, PostgreSQL and Redis",
    version="0.3.0",
    lifespan=lifespan,
)


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


# Keep this route LAST: "/{short_code}" matches any single path segment,
# so routes defined after it (like "/health") would never be reached.
@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    """Redirect the browser from the short link to the original URL."""
    url = crud.get_url_by_code(db, short_code)
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=url.original_url, status_code=302)