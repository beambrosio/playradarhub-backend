from fastapi import APIRouter, Request
from ..services.igdb import fetch_games as igdb_fetch_games
from ..services.steam import fetch_steam_details
from ..logging_config import logger
import re
import asyncio

router = APIRouter()

steam_re = re.compile(r"store\.steampowered\.com\/app\/(\d+)")


@router.get("/api/next_week_release", response_model=list[dict], tags=["Games"])
async def get_next_week_release(request: Request, limit: int = 20, offset: int = 0):
    now = int(__import__('time').time())
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
    http_client = request.app.state.http_client
    games = await igdb_fetch_games(query, http_client)

    async def _attach_steam(game: dict):
        websites = game.get("websites") or []
        if isinstance(websites, list):
            for w in websites:
                url = w.get("url", "") if isinstance(w, dict) else ""
                m = steam_re.search(url)
                if m:
                    appid = m.group(1)
                    steam_data = await fetch_steam_details(http_client, appid)
                    if steam_data:
                        game["steam"] = steam_data
                    return

    tasks = [_attach_steam(game) for game in games]
    if tasks:
        await asyncio.gather(*tasks)
    return games


@router.get("/api/all_games", response_model=list[dict], tags=["Games"])
async def get_all_games(request: Request, limit: int = 20, offset: int = 0, sort_by: str = "hypes desc"):
    logger.info("get_all_games called: sort_by=%s limit=%s offset=%s", sort_by, limit, offset)
    query = f"""
    fields name, cover.url, first_release_date, platforms.name, summary,
           rating, rating_count, genres.name, websites.url, hypes, follows;
    sort {sort_by};
    limit {limit};
    offset {offset};
    """
    http_client = request.app.state.http_client
    games = await igdb_fetch_games(query, http_client)

    async def _attach_steam(game: dict):
        websites = game.get("websites") or []
        if isinstance(websites, list):
            for w in websites:
                url = w.get("url", "") if isinstance(w, dict) else ""
                m = steam_re.search(url)
                if m:
                    appid = m.group(1)
                    steam_data = await fetch_steam_details(http_client, appid)
                    if steam_data:
                        game["steam"] = steam_data
                    return

    tasks = [_attach_steam(game) for game in games]
    if tasks:
        await asyncio.gather(*tasks)
    return games
