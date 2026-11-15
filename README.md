# Scalable URL Shortener

![CI](https://github.com/loki0108/URL-shortener/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Redis](https://img.shields.io/badge/Redis-7-DC382D)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

A URL shortening service (like bit.ly) built with **FastAPI**, **PostgreSQL** and **Redis**.
It turns long URLs into short links, redirects visitors, tracks clicks, and caches frequently
accessed links in Redis for fast lookups. The whole stack runs with a single
`docker compose up`, and every push is tested by a **GitHub Actions** CI pipeline.

---

## Features

- **Shorten URLs**: random 7-character base62 codes (~3.5 trillion combinations)
- **Fast redirects**: HTTP 302 redirect to the original URL
- **Click tracking**: per-link click counter plus a click history (timestamp, user agent, referrer)
- **Stats endpoint**: total clicks, creation time and last click time for any link
- **Redis caching**: cache-aside pattern for redirect lookups, with TTL and LRU eviction
- **Graceful degradation**: if Redis goes down, the service keeps working using PostgreSQL
- **Input validation**: invalid URLs are rejected with `422` by Pydantic
- **Health check**: reports database and cache status
- **Containerized**: app, PostgreSQL and Redis orchestrated with Docker Compose
- **Tested**: 15 pytest tests run on every push via GitHub Actions (Python 3.12 and 3.13)

## Tech Stack

| Layer            | Technology                                   |
|------------------|----------------------------------------------|
| API              | Python, FastAPI, Pydantic, Uvicorn           |
| Database         | PostgreSQL 16, SQLAlchemy 2.0 ORM            |
| Cache            | Redis 7                                      |
| Containerization | Docker, Docker Compose                       |
| Testing          | pytest, FastAPI TestClient                   |
| CI               | GitHub Actions                               |

---

## Architecture

```mermaid
flowchart LR
    U[Client / Browser] -->|HTTP| A[FastAPI app]
    A -->|1. lookup short code| R[(Redis cache)]
    A -->|2. on cache miss| P[(PostgreSQL)]
    A -.->|background task: record click| P
```

### Redirect flow (cache-aside)

```mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI
    participant R as Redis
    participant P as PostgreSQL

    C->>A: GET /aZ3k9Qx
    A->>R: GET url:aZ3k9Qx
    alt Cache HIT
        R-->>A: {id, original_url}
    else Cache MISS
        R-->>A: nil
        A->>P: SELECT ... WHERE short_code = 'aZ3k9Qx'
        P-->>A: row
        A->>R: SET url:aZ3k9Qx (TTL 1h)
    end
    A-->>C: 302 Found (Location: original URL, X-Cache: HIT/MISS)
    A->>P: background: clicks + 1, insert click event
```

---

## Quick Start (Docker)

**Requirements:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
git clone https://github.com/loki0108/URL-shortener.git
cd URL-shortener
docker compose up --build
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI.

Useful commands:

```bash
docker compose up -d          # run in the background
docker compose logs -f app    # follow app logs
docker compose down           # stop (data is kept in the pgdata volume)
docker compose down -v        # stop and delete all data
```

---

## API

| Method | Endpoint               | Description                                  |
|--------|------------------------|----------------------------------------------|
| POST   | `/shorten`             | Create a short link                          |
| GET    | `/{short_code}`        | Redirect to the original URL (302)           |
| GET    | `/stats/{short_code}`  | Click statistics for a short link            |
| GET    | `/health`              | Service, database and cache status           |
| GET    | `/docs`                | Swagger UI (auto-generated API docs)         |

### Shorten a URL

```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/some/very/long/path?query=1"}'
```

```json
{
  "short_code": "aZ3k9Qx",
  "short_url": "http://localhost:8000/aZ3k9Qx",
  "original_url": "https://www.example.com/some/very/long/path?query=1"
}
```

### Follow a short link

```bash
curl -i http://localhost:8000/aZ3k9Qx
```

```
HTTP/1.1 302 Found
location: https://www.example.com/some/very/long/path?query=1
x-cache: MISS        # first request; later requests return HIT
```

### Get click stats

```bash
curl http://localhost:8000/stats/aZ3k9Qx
```

```json
{
  "short_code": "aZ3k9Qx",
  "original_url": "https://www.example.com/some/very/long/path?query=1",
  "clicks": 3,
  "created_at": "2026-11-15T05:40:12.123456Z",
  "last_clicked_at": "2026-11-15T05:42:55.987654Z"
}
```

### Error responses

| Case                        | Status |
|-----------------------------|--------|
| Invalid URL in `/shorten`   | `422`  |
| Unknown short code          | `404`  |
| Database unreachable        | `503` (from `/health`) |

---

## Running Tests

The tests use a temporary **SQLite** database and an in-memory **fake Redis**, so they
need no running services.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
```

The test suite covers URL shortening and validation, short-code collision retries,
redirects, 404s, cache MISS/HIT behaviour, fallback when Redis is down, and click counting.

## Continuous Integration

On every push and pull request, GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)):

1. Runs the full pytest suite on **Python 3.12 and 3.13**
2. If tests pass, builds the Docker image and validates `docker-compose.yml`

---

## Local Development (without Docker for the app)

Run only PostgreSQL and Redis in containers and the app with hot reload:

```bash
docker run --name urlshortener-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=urlshortener -p 5432:5432 -d postgres:16
docker run --name urlshortener-redis -p 6379:6379 -d redis:7 \
  redis-server --maxmemory 100mb --maxmemory-policy allkeys-lru

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Configuration

Settings are read from environment variables (or a `.env` file, see [`.env.example`](.env.example)):

| Variable            | Default                                                    | Description              |
|---------------------|------------------------------------------------------------|--------------------------|
| `DATABASE_URL`      | `postgresql://postgres:postgres@localhost:5432/urlshortener` | PostgreSQL connection    |
| `REDIS_URL`         | `redis://localhost:6379/0`                                 | Redis connection         |
| `CACHE_TTL_SECONDS` | `3600`                                                     | Cache expiry per link    |
| `BASE_URL`          | `http://localhost:8000`                                    | Prefix for short links   |

---

## Project Structure

```
URL-shortener/
├── app/
│   ├── main.py          # FastAPI app and routes
│   ├── config.py        # settings from environment variables
│   ├── database.py      # SQLAlchemy engine, session, Base
│   ├── models.py        # URL and ClickEvent tables
│   ├── schemas.py       # Pydantic request/response models
│   ├── crud.py          # database operations
│   ├── cache.py         # Redis cache-aside helpers
│   └── utils.py         # base62 short-code generator
├── tests/
│   ├── conftest.py      # fixtures: SQLite DB, fake Redis, test client
│   ├── test_api.py      # endpoint tests
│   └── test_utils.py    # short-code generator tests
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

---

## Design Decisions

- **Random base62 codes instead of sequential IDs.** 62 URL-safe characters × 7 positions
  gives ~3.5 trillion codes. Random codes can't be enumerated, so users can't guess other
  people's links by incrementing an ID.
- **Collisions handled by the database.** Instead of "check, then insert" (which races under
  concurrency), the `UNIQUE` index on `short_code` rejects duplicates and the app retries
  with a new code.
- **Cache-aside with TTL and LRU eviction.** Redirects are read-heavy (one write, many reads),
  and popular links get most of the traffic. Redis serves repeat lookups from memory; a 1-hour
  TTL keeps hot links cached while cold links expire, and `allkeys-lru` bounds memory use.
  Short links are immutable, so there is no cache-invalidation problem.
- **Redis is optional, PostgreSQL is required.** Any Redis error is treated as a cache miss,
  so a cache outage slows the service down instead of taking it down.
- **302 instead of 301.** Browsers cache 301 redirects permanently and stop contacting the
  server, which would break click tracking.
- **Click tracking in a background task.** The redirect is sent first; recording the click
  happens afterwards, so analytics never slow down the user.
- **Atomic counter updates.** `UPDATE ... SET clicks = clicks + 1` lets the database
  increment the counter, avoiding lost updates when clicks arrive concurrently.
- **Counter plus event log.** The `clicks` column answers "how many?" instantly, while the
  `click_events` table keeps full history for richer analytics.

## Possible Improvements

- Custom aliases and link expiry
- Rate limiting on `/shorten`
- Database migrations with Alembic
- Integration tests against real PostgreSQL and Redis in CI
- Async database driver (asyncpg) for higher concurrency
- Batching click writes (e.g. counting in Redis, flushing to PostgreSQL periodically)
