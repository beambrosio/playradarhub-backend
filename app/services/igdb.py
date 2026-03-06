import os
import time
import json
from fastapi import HTTPException
from ..logging_config import logger

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")

access_token = None
token_expire_time = 0


async def get_access_token():
    global access_token, token_expire_time
    if access_token and time.time() < token_expire_time:
        return access_token

    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.error("TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET not set in environment")
        raise HTTPException(status_code=500, detail="Missing Twitch client credentials")

    url = "https://id.twitch.tv/oauth2/token"
    params = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
    try:
        # import here to avoid circular at module import
        import httpx
        client = httpx.Client()
        response = client.post(url, params=params)
    except Exception as e:
        logger.exception("Error requesting token from Twitch: %s", e)
        raise HTTPException(status_code=500, detail=f"Twitch token request failed: {e}")

    try:
        data = response.json()
    except Exception:
        text = response.text
        logger.error("Non-JSON response from Twitch token endpoint: status=%s body=%s", response.status_code, text)
        raise HTTPException(status_code=500, detail={"error": "Failed to obtain token", "response_text": text})

    if "access_token" not in data:
        logger.error("Failed to obtain token from Twitch: status=%s body=%s", response.status_code, data)
        raise HTTPException(status_code=500, detail={"error": "Failed to obtain token", "response": data})

    access_token = data["access_token"]
    token_expire_time = time.time() + data.get("expires_in", 0) - 60
    logger.info("Obtained new Twitch access token; expires_in=%s", data.get("expires_in"))
    return access_token


async def fetch_games(query: str, http_client):
    # During local testing, allow returning canned mock data instead of calling IGDB/Twitch.
    if os.environ.get("PLAYRADAR_USE_MOCK_DATA", "").lower() in ("1", "true", "yes"):
        logger.info("Returning mock IGDB data due to PLAYRADAR_USE_MOCK_DATA env var")
        return [
            {
                "id": 123,
                "name": "Mock Game",
                "cover": {"url": "https://images.igdb.com/mock.jpg"},
                "first_release_date": 1670000000,
                "platforms": [{"name": "PC (Windows)"}],
                "summary": "This is a mock game",
                "rating": 85.0,
                "rating_count": 10,
                "genres": [{"name": "Action"}],
                "hypes": 100,
                "follows": 50,
                "websites": [{"url": "https://store.steampowered.com/app/12345"}],
                "steam": {
                    "steam_appid": 12345,
                    "name": "Mock Game",
                    "type": "game",
                    "is_free": False,
                    "required_age": 0,
                    "header_image": "https://cdn.akamai.steamstatic.com/steam/apps/12345/header.jpg",
                    "short_description": "A mock game",
                    "developers": ["Mock Dev"],
                    "publishers": ["Mock Pub"],
                    "genres": [{"id": 1, "description": "Action"}],
                    "categories": [{"id": 1, "description": "Multi-player"}],
                    "metacritic": {"score": 88},
                    "is_dlc": False,
                },
            }
        ]

    token = await get_access_token()
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/plain",
    }
    resp = await http_client.post("https://api.igdb.com/v4/games", content=query, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Error querying IGDB")
    return resp.json()
