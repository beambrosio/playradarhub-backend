from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from ..services.igdb import fetch_games
from ..services.steam import fetch_steam_details
from ..models import Game
import re
import asyncio

router = APIRouter()
steam_re = re.compile(r"store\.steampowered\.com\/app\/(\d+)")

@router.get('/api/game/{game_id}', response_model=Game, tags=['Games'])
async def get_game_detail(request: Request, game_id: int, include_steam: Optional[bool] = True, fields: Optional[str] = None):
    """Get detailed info for a single game by IGDB id. Optionally fetch Steam details if a Steam link is present.

    Query param `fields` is a comma-separated list of extra IGDB fields to include (e.g. "screenshots,videos,release_dates,involved_companies,age_ratings,aggregated_rating,similar_games")."""
    http_client = request.app.state.http_client
    # Base fields always included
    base_fields = [
        "id",
        "name",
        "cover.url",
        "first_release_date",
        "platforms.name",
        "summary",
        "rating",
        "rating_count",
        "genres.name",
        "websites.url",
        "hypes",
        "follows",
    ]
    extra_fields_map = {
        "screenshots": "screenshots.url",
        "videos": "videos.video_id",
        "release_dates": "release_dates.human,release_dates.platform,release_dates.region,release_dates.date",
        "involved_companies": "involved_companies.company.name,involved_companies.role",
        "age_ratings": "age_ratings.rating,age_ratings.category",
        "aggregated_rating": "aggregated_rating,aggregated_rating_count",
        "themes": "themes.name",
        "game_modes": "game_modes.name",
        "keywords": "keywords.name",
        "similar_games": "similar_games.id,similar_games.name,similar_games.cover.url",
    }

    requested_extras = []
    if fields:
        for f in fields.split(','):
            f = f.strip()
            if f in extra_fields_map:
                requested_extras.append(extra_fields_map[f])

    all_fields = base_fields + requested_extras
    fields_str = ", ".join(all_fields)

    # IGDB: fetch by id, include requested fields
    query = f'''
    fields {fields_str};
    where id = {game_id};
    limit 1;
    '''
    games = await fetch_games(query, http_client)
    if not games:
        raise HTTPException(status_code=404, detail='Game not found')
    game = games[0]

    # attach steam details if requested
    if include_steam:
        websites = game.get('websites') or []
        if isinstance(websites, list):
            for w in websites:
                url = w.get('url', '') if isinstance(w, dict) else ''
                m = steam_re.search(url)
                if m:
                    appid = m.group(1)
                    steam_data = await fetch_steam_details(http_client, appid)
                    if steam_data:
                        game['steam'] = steam_data
                    break

    return game
