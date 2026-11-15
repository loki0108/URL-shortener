from datetime import datetime

from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    """Request body for POST /shorten."""
    url: HttpUrl


class URLResponse(BaseModel):
    """What the API returns after shortening a URL."""
    short_code: str
    short_url: str
    original_url: str


class URLStats(BaseModel):
    """Click statistics for one short link."""
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime
    last_clicked_at: datetime | None