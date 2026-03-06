from fastapi import APIRouter
from .games import router as games_router
from .search import router as search_router
from .game_detail import router as game_detail_router

router = APIRouter()
router.include_router(games_router)
router.include_router(search_router)
router.include_router(game_detail_router)
