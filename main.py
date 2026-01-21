from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import httpx
import time
import os

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")

access_token = None
token_expire_time = 0
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient()
    yield
    await http_client.aclose()

app = FastAPI(
    lifespan=lifespan,
    title="PlayRadar Hub API",
    description="API for fetching game information from IGDB",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GameResponse(BaseModel):
    id: int
    name: str
    cover: Optional[dict] = None
    first_release_date: Optional[int] = None
    platforms: Optional[list] = None
    summary: Optional[str] = None
    genres: Optional[list] = None


async def get_access_token():
    global access_token, token_expire_time
    if access_token and time.time() < token_expire_time:
        return access_token

    url = (
        f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}"
        f"&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    )
    response = await http_client.post(url)
    data = response.json()
    if "access_token" not in data:
        raise HTTPException(status_code=500, detail="Falha ao obter token")
    access_token = data["access_token"]
    token_expire_time = time.time() + data.get("expires_in", 0) - 60
    return access_token

@app.get("/api/next_week_release", respose_model=list[dict], tags=["Games"])
async def get_games():
    """
     Get games releasing in the next 7 days.

    Returns up to 100 games sorted by release date.
    """
    token = await get_access_token()
    now = int(time.time())
    one_week_later = now + 7 * 24 * 60 * 60

    query = f"""
    fields name, cover.url, first_release_date, platforms.name, summary, 
           age_ratings.rating, age_ratings.category, genres.name, 
           multiplayer_modes, language_supports;
    where first_release_date >= {now} & first_release_date < {one_week_later};
    sort first_release_date asc;
    limit 100;
    """

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/plain",
    }

    resp = await http_client.post("https://api.igdb.com/v4/games", content=query, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao consultar IGDB")
    return resp.json()

@app.get("/api/all_games", response_model=list[dict], tags=["Games"])
async def get_all_games(limit: int = 20, offset: int = 0, sort_by: str = "hypes desc"):
    """
        Get games with pagination.

        Parameters:
        - limit: Number of games to fetch per page (default: 10).
        - offset: Number of games to skip (default: 0).
        - sort_by: Sorting criteria (default: "hypes desc").
    """

    token = await get_access_token()

    query = f"""
       fields name, cover.url, first_release_date, platforms.name, summary,
              rating, rating_count, genres.name, hypes, follows;
       sort {sort_by};
       limit {limit};
       offset {offset};
       """

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/plain",
    }

    resp = await http_client.post("https://api.igdb.com/v4/games", content=query, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao consultar IGDB")
    return resp.json()
