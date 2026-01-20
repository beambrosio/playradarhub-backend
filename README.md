# playradarhub-backend

Small backend service for PlayRadarHub.

## Overview

Do not keep `client_id` or `client_secret` hardcoded in source. Provide them to the container at build or runtime. Prefer Docker secrets or runtime environment variables over build args for sensitive values.

## Quickstart

Prerequisites:
- Docker
- Python 3.11+ (for local dev)

Build (passing build args — not recommended for long-term secret storage):
```bash
docker build \
  --build-arg CLIENT_ID="$CLIENT_ID" \
  --build-arg CLIENT_SECRET="$CLIENT_SECRET" \
  -t playradarhub-backend .
