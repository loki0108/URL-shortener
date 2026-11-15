from fastapi import FastAPI

app = FastAPI(
    title="URL Shortener",
    description="A scalable URL shortening service built with FastAPI, PostgreSQL and Redis",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Simple endpoint to confirm the service is running."""
    return {"status": "ok"}