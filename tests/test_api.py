import redis

from app import cache, crud

LONG_URL = "https://example.com/some/very/long/path?query=1"


def shorten(client, url=LONG_URL):
    """Helper: create a short link and return the JSON response."""
    response = client.post("/shorten", json={"url": url})
    assert response.status_code == 201
    return response.json()


# ---------- health ----------

def test_health_reports_db_and_cache(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected",
        "cache": "connected",
    }


# ---------- shorten ----------

def test_shorten_returns_short_url(client):
    data = shorten(client)
    assert len(data["short_code"]) == 7
    assert data["short_url"].endswith("/" + data["short_code"])
    assert data["original_url"] == LONG_URL


def test_shorten_rejects_invalid_url(client):
    response = client.post("/shorten", json={"url": "not a url"})
    assert response.status_code == 422


def test_shorten_retries_on_code_collision(client, monkeypatch):
    # Force the generator to return a code that's already taken, then a new one
    codes = iter(["SAMEONE", "SAMEONE", "NEWCODE"])
    monkeypatch.setattr(crud, "generate_short_code", lambda: next(codes))

    first = shorten(client)
    second = shorten(client)  # first attempt collides, retry succeeds

    assert first["short_code"] == "SAMEONE"
    assert second["short_code"] == "NEWCODE"


# ---------- redirect ----------

def test_redirect_to_original_url(client):
    code = shorten(client)["short_code"]
    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == LONG_URL


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/doesnotexist", follow_redirects=False)
    assert response.status_code == 404


# ---------- caching ----------

def test_cache_miss_then_hit(client, fake_redis):
    code = shorten(client)["short_code"]

    first = client.get(f"/{code}", follow_redirects=False)
    second = client.get(f"/{code}", follow_redirects=False)

    assert first.headers["x-cache"] == "MISS"
    assert second.headers["x-cache"] == "HIT"
    assert f"url:{code}" in fake_redis.store


def test_redirect_still_works_when_redis_is_down(client, monkeypatch):
    class BrokenRedis:
        def get(self, *args, **kwargs):
            raise redis.ConnectionError("Redis is down")

        set = ping = get

    monkeypatch.setattr(cache, "redis_client", BrokenRedis())
    code = shorten(client)["short_code"]

    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["x-cache"] == "MISS"
    assert client.get("/health").json()["cache"] == "unavailable"


# ---------- click tracking ----------

def test_new_link_has_zero_clicks(client):
    code = shorten(client)["short_code"]
    stats = client.get(f"/stats/{code}").json()
    assert stats["clicks"] == 0
    assert stats["last_clicked_at"] is None


def test_clicks_are_counted(client):
    code = shorten(client)["short_code"]
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)

    stats = client.get(f"/stats/{code}").json()
    assert stats["clicks"] == 3  # counted on both cache MISS and HITs
    assert stats["last_clicked_at"] is not None


def test_stats_unknown_code_returns_404(client):
    assert client.get("/stats/doesnotexist").status_code == 404