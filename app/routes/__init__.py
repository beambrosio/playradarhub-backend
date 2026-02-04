from fastapi import APIRouter
from .games import router as games_router

router = APIRouter()
router.include_router(games_router)
