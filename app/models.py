from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SteamData(BaseModel):
    steam_appid: Optional[int]
    name: Optional[str]
    type: Optional[str]
    is_free: Optional[bool]
    required_age: Optional[int]
    header_image: Optional[str]
    short_description: Optional[str]
    developers: Optional[List[str]]
    publishers: Optional[List[str]]
    genres: Optional[List[Dict[str, Any]]]
    categories: Optional[List[Dict[str, Any]]]
    metacritic: Optional[Dict[str, Any]]
    is_dlc: Optional[bool] = False
    platforms_supported: Optional[List[str]] = None
    price_overview: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class Game(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    cover: Optional[Dict[str, Any]] = None
    first_release_date: Optional[int] = None
    platforms: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    aggregated_rating: Optional[float] = None
    aggregated_rating_count: Optional[int] = None
    genres: Optional[List[Dict[str, Any]]] = None
    hypes: Optional[int] = None
    follows: Optional[int] = None
    websites: Optional[List[Dict[str, Any]]] = None
    screenshots: Optional[List[Dict[str, Any]]] = None
    videos: Optional[List[Dict[str, Any]]] = None
    release_dates: Optional[List[Dict[str, Any]]] = None
    involved_companies: Optional[List[Dict[str, Any]]] = None
    age_ratings: Optional[List[Dict[str, Any]]] = None
    themes: Optional[List[Dict[str, Any]]] = None
    game_modes: Optional[List[Dict[str, Any]]] = None
    keywords: Optional[List[Dict[str, Any]]] = None
    similar_games: Optional[List[Dict[str, Any]]] = None
    steam: Optional[SteamData] = None
    is_dlc: Optional[bool] = False

    class Config:
        extra = "allow"
        allow_population_by_field_name = True
