"""Search hotels via SerpAPI Google Hotels. Returns list of hotel options with fallback stub."""
from __future__ import annotations

import logging
from typing import Any

from config import CURRENCY, SERPAPI_KEY

logger = logging.getLogger(__name__)

STUB_HOTELS = [
    {"name": "Hotel ABC", "price_per_night": 112, "stars": 4, "rating": 9.2, "discount": 25},
    {"name": "Marina View", "price_per_night": 98, "stars": 4, "rating": 8.9, "discount": None},
    {"name": "City Center", "price_per_night": 135, "stars": 4, "rating": 9.5, "discount": None},
    {"name": "Plaza Suite", "price_per_night": 89, "stars": 4, "rating": 8.7, "discount": None},
    {"name": "Royal Beach", "price_per_night": 145, "stars": 4, "rating": 9.1, "discount": None},
]


def search_hotels(
    query: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    stars: int = 4,
    currency: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return list of hotel options. Each dict: name, price_per_night, stars, rating, discount (optional).
    On API error or missing key, returns STUB_HOTELS.
    """
    currency = currency or CURRENCY
    if not SERPAPI_KEY:
        logger.warning("SERPAPI_KEY missing, using stub hotels")
        return STUB_HOTELS.copy()

    try:
        from serpapi import GoogleSearch
    except ImportError:
        logger.warning("serpapi not installed, using stub hotels")
        return STUB_HOTELS.copy()

    # hotel_class: 2=2*, 3=3*, 4=4*, 5=5*
    params = {
        "engine": "google_hotels",
        "api_key": SERPAPI_KEY,
        "q": query,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "currency": currency,
        "hl": "en",
        "hotel_class": str(stars),
    }

    try:
        search = GoogleSearch(params)
        data = search.get_dict()
    except Exception as e:
        logger.exception("SerpAPI hotels request failed: %s", e)
        return STUB_HOTELS.copy()

    if data.get("search_metadata", {}).get("status") != "Success":
        logger.warning("SerpAPI hotels status not Success, using stub")
        return STUB_HOTELS.copy()

    # Prefer "properties" then "ads" (Google Hotels response structure)
    items = data.get("properties") or data.get("ads") or []
    out: list[dict[str, Any]] = []
    for i, item in enumerate(items[:10]):
        try:
            name = item.get("name", "Hotel")
            # price: properties use rate_per_night.lowest / extracted_lowest, ads use price/extracted_price
            price = None
            if "rate_per_night" in item:
                rn = item["rate_per_night"]
                price = rn.get("extracted_lowest") or (rn.get("lowest") and _extract_price(rn["lowest"]))
            if price is None:
                price = item.get("extracted_price") or _extract_price(item.get("price", "0"))
            stars_val = item.get("hotel_class") or item.get("extracted_hotel_class")
            if isinstance(stars_val, str) and "star" in stars_val.lower():
                stars_val = 4
            stars_val = int(stars_val) if stars_val else 4
            rating = item.get("overall_rating") or (8.5 + (i % 5) * 0.1)
            if isinstance(rating, (int, float)):
                rating = round(rating, 1)
            out.append({
                "name": name,
                "price_per_night": int(price) if price else 0,
                "stars": stars_val,
                "rating": rating,
                "discount": None,
            })
        except (TypeError, KeyError, ValueError) as e:
            logger.debug("Skip hotel item %s: %s", item, e)
            continue

    if not out:
        return STUB_HOTELS.copy()
    return out


def _extract_price(s: str):
    """Try to get numeric price from string like '$112' or '98€'."""
    if s is None:
        return None
    import re
    m = re.search(r"[\d\s]+", str(s))
    if m:
        return int(m.group(0).replace(" ", ""))
    return None
