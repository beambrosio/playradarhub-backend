from fastapi import FastAPI
from contextlib import asynccontextmanager
import httpx
from .logging_config import logger

http_client: httpx.AsyncClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient()
    app.state.http_client = http_client
    yield
    if http_client is not None:
        await http_client.aclose()


def create_app() -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware
    from .routes import router

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
