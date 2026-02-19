"""AI analysis of flight+hotel combos and savings via OpenAI. Returns structured dict with fallback."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Fallback when OpenAI fails or key missing
def _stub_combos(flights: list, hotels: list, nights: int, budget: Optional[int]) -> dict:
    """Build 2 best combos from first flight/hotel entries."""
    combos = []
    if flights and hotels:
        f1, f2 = flights[0], flights[1] if len(flights) > 1 else flights[0]
        h1, h2 = hotels[0], hotels[1] if len(hotels) > 1 else hotels[0]
        total1 = f1.get("total_price", 0) + (h1.get("price_per_night", 0) * nights)
        total2 = f2.get("total_price", 0) + (h2.get("price_per_night", 0) * nights)
        pct = 0
        if budget and total1 < budget:
            pct = round((1 - total1 / budget) * 100)
        combos = [
            {"flight_index": 0, "hotel_index": 0, "total": total1, "savings_percent": pct, "label": "экономия 18%"},
            {"flight_index": 1, "hotel_index": 1, "total": total2, "savings_percent": 0, "label": "лучшее соотношение цена/качество"},
        ]
    return {"best_combos": combos, "recommendation": "Первый вариант — лучшая экономия, второй — баланс цены и качества."}


def analyze_combos(
    flights: list[dict],
    hotels: list[dict],
    nights: int,
    budget: Optional[int] = None,
) -> dict:
    """
    Return dict with:
      - best_combos: list of { flight_index, hotel_index, total, savings_percent, label }
      - recommendation: short text
    Uses OpenAI JSON mode when key present; otherwise stub.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY missing, using stub combos")
        return _stub_combos(flights, hotels, nights, budget)

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai not installed, using stub combos")
        return _stub_combos(flights, hotels, nights, budget)

    # Build compact summary for prompt
    fl = [{"i": i, "airline": f.get("airline"), "total": f.get("total_price"), "rating": f.get("rating")} for i, f in enumerate(flights[:5])]
    ho = [{"i": i, "name": h.get("name"), "price_per_night": h.get("price_per_night"), "rating": h.get("rating")} for i, h in enumerate(hotels[:5])]

    prompt = f"""Даны варианты перелётов и отелей. Рассчитай 2 лучших комбо (перелёт + отель) по итоговой цене за поездку.
Перелёты (round-trip): {json.dumps(fl, ensure_ascii=False)}
Отели (цена за ночь): {json.dumps(ho, ensure_ascii=False)}
Количество ночей: {nights}
Бюджет (евро, опционально): {budget or 'не указан'}

Верни ТОЛЬКО валидный JSON без markdown, в формате:
{{"best_combos": [{{"flight_index": 0, "hotel_index": 0, "total": 1256, "savings_percent": 18, "label": "экономия 18%"}}, ...], "recommendation": "краткая рекомендация одним предложением"}}
Должно быть ровно 2 элемента в best_combos. total = цена перелёта + (цена за ночь * ночей). savings_percent — если есть бюджет, иначе 0."""

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        combos = data.get("best_combos") or []
        if len(combos) < 2:
            return _stub_combos(flights, hotels, nights, budget)
        return {
            "best_combos": combos[:2],
            "recommendation": data.get("recommendation") or _stub_combos(flights, hotels, nights, budget)["recommendation"],
        }
    except Exception as e:
        logger.exception("OpenAI analyze_combos failed: %s", e)
        return _stub_combos(flights, hotels, nights, budget)
