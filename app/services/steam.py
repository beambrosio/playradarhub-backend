import asyncio
from ..logging_config import logger

async def fetch_steam_details(http_client, appid: str) -> dict | None:
    """
    Fetch Steam store details for a given Steam app id using the public store API.
    Returns the 'data' block from the Steam API response if available, otherwise None.
    Enriches data with is_dlc, platforms (mapping from Steam response), and price_overview when present.
    """
    try:
        resp = await http_client.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&l=en&cc=us")
        if resp.status_code != 200:
            return None
        data = resp.json()
        entry = data.get(str(appid))
        if not entry or not entry.get("success"):
            return None
        info = entry.get("data") or {}
        # Detect DLC: Steam includes a 'type' field and a 'dlc' array on base games
        info["is_dlc"] = bool(info.get("type") == "dlc")
        # Map platforms: Steam returns a 'platforms' dict with 'windows', 'mac', 'linux' booleans
        platforms = info.get("platforms")
        if isinstance(platforms, dict):
            mapped = [k for k, v in platforms.items() if v]
            info["platforms_supported"] = mapped
        # price_overview includes price and currency information when available
        price = info.get("price_overview")
        if price:
            info["price_overview"] = price
        return info
    except Exception:
        logger.exception("Error fetching steam details for appid=%s", appid)
        return None
