import uvicorn
from fastapi import FastAPI
from app import create_app

app = create_app()


async def get_access_token():
    global access_token, token_expire_time
    if access_token and time.time() < token_expire_time:
        return access_token

    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.error("TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET not set in environment")
        raise HTTPException(status_code=500, detail="Missing Twitch client credentials")

    url = f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    payload = ""
    headers = {}

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info(f"response: {response}")
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


def build_headers(token: str) -> dict:
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/plain",
    }


async def fetch_steam_details(appid: str) -> dict | None:
    """
    Fetch Steam store details for a given Steam app id using the public store API.
    Returns the 'data' block from the Steam API response if available, otherwise None.
    Adds an 'is_dlc' boolean when applicable.
    """
    try:
        resp = await http_client.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&l=en&cc=us")
        if resp.status_code != 200:
            return None
        data = resp.json()
        entry = data.get(str(appid))
        if not entry or not entry.get("success"):
            return None
        info = entry.get("data") or {}
        # Detect DLC: Steam includes a 'type' field and a 'dlc' array on base games
        is_dlc = (info.get("type") == "dlc") or (isinstance(info.get("dlc"), list) and len(info.get("dlc")) == 0 and info.get("type") == "dlc")
        # More reliable: if 'type' == 'dlc' then it's a DLC; otherwise if the app has a parent package or similar, classify accordingly
        info["is_dlc"] = bool(info.get("type") == "dlc")
        return info
    except Exception:
        return None


async def fetch_games(query: str) -> list[dict]:
    logging.info("fetch_games")
    token = await get_access_token()
    # do not print tokens
    headers = build_headers(token)
    resp = await http_client.post("https://api.igdb.com/v4/games", content=query, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Error querying IGDB")
    games = resp.json()

    # Enrich returned games with Steam data when a Steam store URL is present in IGDB 'websites'
    steam_re = re.compile(r"store\\.steampowered\\.com\\/app\\/(\\d+)")
    async def _attach_steam(game: dict):
        websites = game.get("websites") or []
        if isinstance(websites, list):
            for w in websites:
                url = w.get("url", "") if isinstance(w, dict) else ""
                m = steam_re.search(url)
                if m:
                    appid = m.group(1)
                    steam_data = await fetch_steam_details(appid)
                    if steam_data:
                        game["steam"] = steam_data
                    return

    tasks = [_attach_steam(game) for game in games]
    if tasks:
        await asyncio.gather(*tasks)
    return games


@app.get("/api/next_week_release", response_model=list[dict], tags=["Games"])
async def get_next_week_release(limit: int = 20, offset: int = 0):
    """
    Get games releasing in the next 7 days with pagination.

    Parameters:
    - limit: Number of games to fetch per page (default: 20).
    - offset: Number of games to skip (default: 0).

    Returns up to the specified number of games sorted by release date.
    """
    now = int(time.time())
    one_week_later = now + 7 * 24 * 60 * 60

    query = f"""
    fields name, cover.url, first_release_date, platforms.name, summary,
           age_ratings.rating, age_ratings.category, genres.name, websites.url,
           multiplayer_modes, language_supports;
    where first_release_date >= {now} & first_release_date < {one_week_later};
    sort first_release_date asc;
    limit {limit};
    offset {offset};
    """
    return await fetch_games(query)


@app.get("/api/all_games", response_model=list[dict], tags=["Games"])
async def get_all_games(limit: int = 20, offset: int = 0, sort_by: str = "hypes desc"):
    """
    Get games with pagination.

    Parameters:
    - limit: Number of games to fetch per page (default: 10).
    - offset: Number of games to skip (default: 0).
    - sort_by: Sorting criteria (default: "hypes desc").
    """
    logger.info("get_all_games called: sort_by=%s limit=%s offset=%s", sort_by, limit, offset)
    query = f"""
    fields name, cover.url, first_release_date, platforms.name, summary,
           rating, rating_count, genres.name, websites.url, hypes, follows;
    sort {sort_by};
    limit {limit};
    offset {offset};
    """
    return await fetch_games(query)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
