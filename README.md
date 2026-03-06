# PlayRadararHub Backend

Small FastAPI backend for PlayRadarHub that queries IGDB and enriches results with Steam store data.

## Overview

- The service queries IGDB using Twitch client-credentials (TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET) and caches the short-lived OAuth token in memory.
- It enriches IGDB game objects by detecting Steam store URLs in IGDB website entries and attaching public Steam store metadata (including an `is_dlc` flag when available).
- Uses a single shared httpx.AsyncClient created at application startup and closed on shutdown.

## Features

- Endpoints:
  - `GET /api/all_games` — paginated, sortable list of games (enriched with Steam when available)
  - `GET /api/next_week_release` — games releasing in the next 7 days
- Deployment helper: `cloudbuild.yaml` builds and deploys to Google Cloud Run and configures secrets.

## Quickstart (local)

Prerequisites:
- Python 3.11+

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set required env vars and run (PowerShell):

```powershell
$env:TWITCH_CLIENT_ID = 'your_client_id'
$env:TWITCH_CLIENT_SECRET = 'your_client_secret'
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Or Bash / macOS / WSL:

```bash
export TWITCH_CLIENT_ID="your_client_id"
export TWITCH_CLIENT_SECRET="your_client_secret"
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Quick smoke tests:

```bash
curl -s 'http://127.0.0.1:8080/api/all_games?limit=1' | jq
curl -s 'http://127.0.0.1:8080/api/next_week_release?limit=5' | jq
```

## Docker

Build (passing build args — not recommended for sensitive values):

```bash
docker build \
  --build-arg CLIENT_ID="$CLIENT_ID" \
  --build-arg CLIENT_SECRET="$CLIENT_SECRET" \
  -t playradarhub-backend .
```

## CI/CD

- `cloudbuild.yaml` builds and deploys to Cloud Run and maps secrets (TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, APITUBE_API_KEY) via Secret Manager.
- Example GitHub Actions workflow to inject a GCP service account key and run `gcloud builds submit` was added at `.github/workflows/deploy-cloudrun.yml`.

## Developer notes / conventions

- Secrets: Do not commit secrets to source. Provide them via runtime env vars or Cloud Run secrets.
- Token caching: The Twitch token is cached in-memory for the lifetime of the process with a conservative 60s buffer before expiry.
- HTTP client: A shared `httpx.AsyncClient` is created during app lifespan and attached to `app.state.http_client` for handlers to use.
- Steam enrichment: The app looks for Steam store URLs (`store.steampowered.com/app/<appid>`) in IGDB website entries and attaches Steam store `data` under `game["steam"]` when found.

## Files added during refactor

- `main.py` — application entrypoint (calls `app.create_app()`)
- `app/` — package containing modularized code:
  - `app/__init__.py` — FastAPI app factory and lifespan
  - `app/routes/games.py` — API route handlers
  - `app/services/igdb.py` — IGDB token handling and query helper
  - `app/services/steam.py` — Steam enrichment helper
- `logging_config.py` — centralized logging setup
- `.github/copilot-instructions.md` — Copilot guidance (generated)
- `.github/workflows/deploy-cloudrun.yml` — example CI workflow

## Next steps / suggestions

- Add tests (pytest + pytest-asyncio) and mock external APIs with httpx.MockTransport.
- Add caching (Redis or in-process TTL cache) for Steam responses and IGDB queries to reduce API usage.
- Add structured models (pydantic) for responses if you want stricter contracts with the frontend.

---

Created & Developed by: Beatriz Ambrosio