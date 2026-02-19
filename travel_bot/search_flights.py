"""Search flights via SerpAPI Google Flights. Returns list of flight options with fallback stub."""
from __future__ import annotations

import logging
from typing import Any

from config import CURRENCY, SERPAPI_KEY

logger = logging.getLogger(__name__)

# Stub data when API fails or key missing (plan: fallback so UI is always testable)
STUB_FLIGHTS = [
    {"airline": "Ryanair", "price_per_person": 89, "total_price": 178, "duration_min": 150, "stops": 1, "rating": 4.2},
    {"airline": "Aeroflot", "price_per_person": 145, "total_price": 290, "duration_min": 195, "stops": 0, "rating": 4.7},
    {"airline": "Turkish Airlines", "price_per_person": 112, "total_price": 224, "duration_min": 250, "stops": 1, "rating": 4.5},
]


def search_flights(
    origin_iata: str,
    destination_iata: str,
    outbound_date: str,
    return_date: str,
    adults: int = 2,
    currency: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return list of flight options. Each dict: airline, price_per_person, total_price,
    duration_min, stops, rating.
    On API error or missing key, returns STUB_FLIGHTS (with total_price adjusted for adults).
    """
    currency = currency or CURRENCY
    if not SERPAPI_KEY:
        logger.warning("SERPAPI_KEY missing, using stub flights")
        return _stub_with_adults(adults)

    try:
        from serpapi import GoogleSearch
    except ImportError:
        logger.warning("serpapi not installed, using stub flights")
        return _stub_with_adults(adults)

    params = {
        "engine": "google_flights",
        "api_key": SERPAPI_KEY,
        "departure_id": origin_iata,
        "arrival_id": destination_iata,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "adults": adults,
        "currency": currency,
        "type": "1",  # round trip
        "hl": "en",
    }

    try:
        search = GoogleSearch(params)
        data = search.get_dict()
    except Exception as e:
        logger.exception("SerpAPI flights request failed: %s", e)
        return _stub_with_adults(adults)

    if data.get("search_metadata", {}).get("status") != "Success":
        logger.warning("SerpAPI flights status not Success, using stub")
        return _stub_with_adults(adults)

    best = data.get("best_flights") or []
    out: list[dict[str, Any]] = []
    for i, item in enumerate(best[:10]):
        try:
            price_total = item.get("price") or 0
            total_duration = item.get("total_duration") or 0
            flights_legs = item.get("flights") or []
            airline = flights_legs[0].get("airline", "Unknown") if flights_legs else "Unknown"
            stops = max(0, len(flights_legs) - 1)
            out.append({
                "airline": airline,
                "price_per_person": price_total // adults if adults else price_total,
                "total_price": price_total,
                "duration_min": total_duration,
                "stops": stops,
                "rating": 4.0 + (i % 3) * 0.2,
            })
        except (TypeError, KeyError) as e:
            logger.debug("Skip flight item %s: %s", item, e)
            continue

    if not out:
        return _stub_with_adults(adults)
    return out


def _stub_with_adults(adults: int) -> list[dict[str, Any]]:
    """Return stub list with total_price scaled by adults (stub assumes 2)."""
    base = 2
    result = []
    for f in STUB_FLIGHTS:
        total = f["price_per_person"] * adults
        result.append({
            **f,
            "total_price": total,
        })
    return result
