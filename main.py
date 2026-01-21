from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/next_week_release")
async def get_games():
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

@app.get("/api/best_rating_week_release")
async def get_best_rated_games():
    token = await get_access_token()
    now = int(time.time())
    one_week_later = now + 7 * 24 * 60 * 60

    query = f"""
    fields name, cover.url, first_release_date, platforms.name, summary, 
           total_rating, total_rating_count, genres.name;
    where first_release_date >= {now} & first_release_date < {one_week_later}
          & total_rating != null;
    sort total_rating desc;
    limit 10;
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