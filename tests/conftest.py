import os

# Must be set BEFORE importing the app, because config is read at import time.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # never actually contacted

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import cache  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


class FakeRedis:
    """Minimal in-memory stand-in for Redis (only the methods our app uses)."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value

    def ping(self):
        return True


@pytest.fixture
def fake_redis(monkeypatch):
    """Replace the real Redis client with FakeRedis for one test."""
    fake = FakeRedis()
    monkeypatch.setattr(cache, "redis_client", fake)
    return fake


@pytest.fixture
def client(fake_redis):
    """A test client with fresh, empty tables for every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)