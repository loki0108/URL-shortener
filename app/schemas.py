from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    """Request body for POST /shorten."""
    url: HttpUrl


class URLResponse(BaseModel):
    """What the API returns after shortening a URL."""
    short_code: str
    short_url: str
    original_url: str