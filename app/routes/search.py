from fastapi import APIRouter, Request
from ..services.igdb import fetch_games
from ..logging_config import logger
from ..models import Game
from typing import List

router = APIRouter()

@router.get('/api/search', response_model=List[Game], tags=['Games'])
async def search_games(request: Request, q: str, limit: int = 1, offset: int = 0):
    """Search games by name using IGDB's search capabilities (fuzzy)."""
    http_client = request.app.state.http_client
    # IGDB search: search "name" field and return relevant fields
    query = f'''
    search "{q}";
    fields id, name, cover.url, first_release_date, platforms.name, summary, rating, rating_count, genres.name, websites.url, hypes, follows;
    limit {limit};
    offset {offset};
    '''
    games = await fetch_games(query, http_client)
    return games
