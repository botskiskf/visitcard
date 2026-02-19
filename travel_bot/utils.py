"""Parsing of natural-language search queries: dates, cities, adults, stars, budget."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

# City/region name (RU/EN) -> IATA airport code for SerpAPI
CITY_TO_IATA = {
    "москва": "SVO",
    "moscow": "SVO",
    "барселона": "BCN",
    "barcelona": "BCN",
    "париж": "CDG",
    "paris": "CDG",
    "амстердам": "AMS",
    "amsterdam": "AMS",
    "рим": "FCO",
    "rome": "FCO",
    "мадрид": "MAD",
    "madrid": "MAD",
    "лондон": "LHR",
    "london": "LHR",
    "мехелен": "BRU",
    "mechelen": "BRU",
    "брюссель": "BRU",
    "brussels": "BRU",
    "берлин": "BER",
    "berlin": "BER",
    "прага": "PRG",
    "prague": "PRG",
    "вена": "VIE",
    "vienna": "VIE",
    "милан": "MXP",
    "milan": "MXP",
    "лиссабон": "LIS",
    "lisbon": "LIS",
    "афины": "ATH",
    "athens": "ATH",
    "istanbul": "IST",
    "стамбул": "IST",
    "киев": "KBP",
    "kyiv": "KBP",
    "kiev": "KBP",
}

# Russian month names -> number
RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    "янв": 1, "фев": 2, "мар": 3, "апр": 4, "июн": 6, "июл": 7, "авг": 8,
    "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
}


@dataclass
class ParsedQuery:
    """Structured result of parsing a search query."""
    destination: str
    destination_iata: str
    origin_iata: str
    outbound_date: str
    return_date: str
    adults: int
    stars: int
    budget: Optional[int]
    raw: str


def _resolve_iata(city: str) -> str:
    """Return IATA code for city name or empty string if unknown."""
    key = city.strip().lower()
    return CITY_TO_IATA.get(key, "")


def _parse_dates_from_text(text: str) -> Optional[Tuple[str, str]]:
    """
    Try to extract date range from text. Returns (outbound_date, return_date) in YYYY-MM-DD
    or None. Uses current year if not specified; if range is in the past, uses next year.
    """
    text_lower = text.lower()
    now = datetime.now()
    year = now.year

    # Pattern: "15-22 июля" or "15–22 июля" or "15 - 22 июля"
    for month_name, month_num in RU_MONTHS.items():
        if month_name not in text_lower:
            continue
        # e.g. "15-22 июля" -> 15, 22, 7
        match = re.search(r"(\d{1,2})\s*[-–—]\s*(\d{1,2})\s*" + re.escape(month_name), text_lower, re.I)
        if match:
            d1, d2 = int(match.group(1)), int(match.group(2))
            try:
                start = datetime(year, month_num, d1)
                end = datetime(year, month_num, d2)
                if end <= start:
                    continue
                if end < now:
                    start = datetime(year + 1, month_num, d1)
                    end = datetime(year + 1, month_num, d2)
                return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # ISO-style: 2026-07-15/2026-07-22 or 15.07.2026 - 22.07.2026
    iso = re.search(r"(\d{4})-(\d{2})-(\d{2})\s*[/\-]\s*(\d{4})-(\d{2})-(\d{2})", text)
    if iso:
        y1, m1, d1 = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
        y2, m2, d2 = int(iso.group(4)), int(iso.group(5)), int(iso.group(6))
        try:
            start = datetime(y1, m1, d1)
            end = datetime(y2, m2, d2)
            if end > start:
                return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def _parse_adults(text: str) -> int:
    """Extract number of adults (default 2)."""
    # "2 человека", "2 чел", "2 adults", "2 человека"
    m = re.search(r"(\d+)\s*(?:человек|чел|adults?|passengers?)", text, re.I)
    if m:
        n = int(m.group(1))
        return max(1, min(n, 9))
    m = re.search(r"\b(\d+)\s*[чч]?\s*$", text)
    if m:
        return max(1, min(int(m.group(1)), 9))
    return 2


def _parse_stars(text: str) -> int:
    """Extract hotel stars 2-5 (default 4)."""
    m = re.search(r"(\d)\s*\*|(\d)\s*звезд|(\d)\s*star", text, re.I)
    if m:
        n = int(m.group(1) or m.group(2) or m.group(3))
        return max(2, min(n, 5))
    return 4


def _parse_budget(text: str) -> Optional[int]:
    """Extract budget in euros (number before € or 'евро')."""
    m = re.search(r"(\d[\d\s]*)\s*[€€]|(\d[\d\s]*)\s*евро|(\d[\d\s]*)\s*eur", text, re.I)
    if m:
        raw = (m.group(1) or m.group(2) or m.group(3)).replace(" ", "")
        return int(raw)
    return None


def _find_destination_city(text: str) -> str:
    """
    Heuristic: first known city name that appears in the query (as destination).
    Skip common origin cities if we have a default origin.
    """
    words = re.split(r"[\s,]+", text)
    for i, w in enumerate(words):
        key = w.lower().strip()
        if key in CITY_TO_IATA:
            return w.strip()
    # Try two-word "City Name"
    for i in range(len(words) - 1):
        two = (words[i] + " " + words[i + 1]).lower()
        if two in CITY_TO_IATA:
            return (words[i] + " " + words[i + 1]).strip()
    return ""


def parse_query(raw: str, origin_iata: str) -> Optional[ParsedQuery]:
    """
    Parse natural language query into structured data.
    Returns None if destination or dates could not be determined.
    """
    raw = raw.strip()
    if not raw:
        return None

    destination = _find_destination_city(raw)
    destination_iata = _resolve_iata(destination) if destination else ""
    if not destination_iata:
        return None

    dates = _parse_dates_from_text(raw)
    if not dates:
        return None

    outbound_date, return_date = dates
    adults = _parse_adults(raw)
    stars = _parse_stars(raw)
    budget = _parse_budget(raw)

    return ParsedQuery(
        destination=destination,
        destination_iata=destination_iata,
        origin_iata=origin_iata,
        outbound_date=outbound_date,
        return_date=return_date,
        adults=adults,
        stars=stars,
        budget=budget,
        raw=raw,
    )
