"""Provedores de preço do TripWatch AI.

- ``demo``: simulador determinístico (funciona sem chave, ideal para o preview).
- ``serpapi``: Google Flights / Google Hotels reais via SerpAPI (SERPAPI_KEY).

A interface é a mesma para os dois: ``search(watch) -> PriceResult``.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from db import demo_price


class ProviderError(RuntimeError):
    pass


@dataclass
class PriceResult:
    price: float
    currency: str
    provider: str
    meta: dict[str, Any] = field(default_factory=dict)


class BaseProvider:
    name = "base"

    def search(self, watch: dict) -> PriceResult:  # pragma: no cover
        raise NotImplementedError

    def status(self) -> dict:
        return {"name": self.name, "configured": True, "detail": ""}


class DemoProvider(BaseProvider):
    name = "demo"

    def search(self, watch: dict) -> PriceResult:
        price, meta = demo_price(watch)
        return PriceResult(price=price, currency=watch["currency"], provider="demo", meta=meta)

    def status(self) -> dict:
        return {
            "name": "demo",
            "configured": True,
            "detail": "Simulador local determinístico, sem custo. Configure SERPAPI_KEY para dados reais.",
        }


class SerpApiProvider(BaseProvider):
    name = "serpapi"

    def __init__(self) -> None:
        self.api_key = os.environ.get("SERPAPI_KEY", "").strip()
        self.currency = os.environ.get("SERPAPI_CURRENCY", "BRL")
        self.hl = os.environ.get("SERPAPI_HL", "pt-br")
        self.gl = os.environ.get("SERPAPI_GL", "br")

    def status(self) -> dict:
        return {
            "name": "serpapi",
            "configured": bool(self.api_key),
            "detail": "Google Flights + Google Hotels em tempo real (SerpAPI)." if self.api_key else "Defina SERPAPI_KEY.",
        }

    def _get(self, params: dict) -> dict:
        if not self.api_key:
            raise ProviderError("SERPAPI_KEY ausente")
        params = {**params, "api_key": self.api_key, "hl": self.hl, "gl": self.gl, "currency": self.currency}
        url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "TripWatchAI/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "ignore")[:300]
            raise ProviderError(f"SerpAPI HTTP {exc.code}: {detail}") from exc
        except Exception as exc:  # rede, timeout, JSON inválido
            raise ProviderError(str(exc)) from exc

    def search(self, watch: dict) -> PriceResult:
        if watch["kind"] == "flight":
            cabin_map = {"economy": 1, "premium_economy": 2, "business": 3, "first": 4}
            params = {
                "engine": "google_flights",
                "departure_id": watch.get("origin") or "",
                "arrival_id": watch.get("destination") or "",
                "outbound_date": watch.get("depart_date") or "",
                "adults": 1,
                "travel_class": cabin_map.get(watch.get("cabin") or "economy", 1),
            }
            if watch.get("return_date"):
                params["return_date"] = watch["return_date"]
            payload = self._get(params)
            price, offer = _parse_flights(payload)
        else:
            params = {
                "engine": "google_hotels",
                "q": watch.get("hotel_name") or watch.get("city") or watch.get("title") or "",
                "check_in_date": watch.get("checkin") or "",
                "check_out_date": watch.get("checkout") or "",
                "adults": watch.get("guests") or 1,
                "rooms": watch.get("rooms") or 1,
            }
            payload = self._get(params)
            price, offer = _parse_hotels(payload)

        if price is None:
            raise ProviderError("A SerpAPI respondeu sem preço utilizável para esta busca.")
        return PriceResult(
            price=round(float(price), 2),
            currency=self.currency,
            provider="serpapi",
            meta={"mode": "live", "offer": offer, "note": "Preço real via Google Flights/Hotels (SerpAPI)."},
        )


def _first_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit() or ch in ".,")
        if not digits:
            return None
        digits = digits.replace(".", "").replace(",", ".") if digits.count(",") == 1 and digits.count(".") == 0 else digits.replace(",", "")
        try:
            return float(digits)
        except ValueError:
            return None
    return None


def _parse_flights(payload: dict) -> tuple[float | None, dict]:
    candidates: list[float] = []
    offer: dict = {}
    for item in payload.get("best_flights") or []:
        price = _first_number(item.get("price"))
        if price:
            candidates.append(price)
            if not offer:
                legs = item.get("flights") or []
                first = legs[0] if legs else {}
                offer = {
                    "airline": first.get("airline"),
                    "flight_number": first.get("flight_number"),
                    "departure": (first.get("departure_airport") or {}).get("id"),
                    "arrival": (first.get("arrival_airport") or {}).get("id"),
                    "duration": first.get("duration"),
                    "stops": max(0, len(legs) - 1),
                }
    insights = payload.get("price_insights") or {}
    low = _first_number(insights.get("lowest_price"))
    if low:
        candidates.append(low)
    if not candidates:
        for item in payload.get("other_flights") or []:
            price = _first_number(item.get("price"))
            if price:
                candidates.append(price)
    return (min(candidates) if candidates else None), offer


def _parse_hotels(payload: dict) -> tuple[float | None, dict]:
    candidates: list[float] = []
    offer: dict = {}
    for item in payload.get("properties") or []:
        rate = item.get("rate_per_night") or {}
        price = _first_number(rate.get("price") or item.get("price"))
        if price:
            candidates.append(price)
            if not offer:
                offer = {
                    "hotel": item.get("name") or item.get("hotel_name"),
                    "rating": item.get("overall_score") or item.get("rating"),
                    "reviews": item.get("reviews"),
                    "link": item.get("link"),
                }
    return (min(candidates) if candidates else None), offer


def get_provider() -> BaseProvider:
    forced = os.environ.get("TRIPWATCH_PROVIDER", "auto").strip().lower()
    if forced == "demo":
        return DemoProvider()
    if forced == "serpapi":
        return SerpApiProvider()
    if os.environ.get("SERPAPI_KEY"):
        return SerpApiProvider()
    return DemoProvider()


def provider_status() -> dict:
    provider = get_provider()
    status = provider.status()
    status["active"] = provider.name
    status["serpapi_key_present"] = bool(os.environ.get("SERPAPI_KEY"))
    status["llm_configured"] = bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or (os.environ.get("LLM_API_KEY") and os.environ.get("LLM_BASE_URL"))
    )
    return status
