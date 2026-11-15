from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (import registers the models with Base)
from app.database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once at startup: create tables if they don't exist yet
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="URL Shortener",
    description="A scalable URL shortening service built with FastAPI, PostgreSQL and Redis",
    version="0.2.0",
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