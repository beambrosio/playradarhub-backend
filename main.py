from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time
import os


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _twitch_credentials():

    CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")

    return CLIENT_ID, CLIENT_SECRET


CLIENT_ID, CLIENT_SECRET = _twitch_credentials()


access_token = None
token_expire_time = 0


async def get_access_token():
    global access_token, token_expire_time
    if access_token and time.time() < token_expire_time:
        return access_token

    url = (
        f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}"
        f"&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        data = response.json()
        if "access_token" not in data:
            raise HTTPException(status_code=500, detail="Falha ao obter token")
        access_token = data["access_token"]
        expires_in = data.get("expires_in", 0)
        token_expire_time = time.time() + expires_in - 60
        return access_token

@app.get("/api/games")
async def get_games():
    token = await get_access_token()

    now = int(time.time())
    one_week_later = now + 7 * 24 * 60 * 60

    query = f"""
    fields name, cover.url, first_release_date, platforms.name, summary;
    where first_release_date >= {now} & first_release_date < {one_week_later};
    sort first_release_date asc;
    limit 20;
    """

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/plain",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.igdb.com/v4/games", content=query, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Erro ao consultar IGDB")
        games = resp.json()
        return games


if __name__ == "__main__":
    import uvicorn
    # Run without auto-reload so the debugger attaches to the same process
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")