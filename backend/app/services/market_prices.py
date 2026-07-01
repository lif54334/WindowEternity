from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

import httpx

from app.core.config import DEFAULT_USER_AGENT, GOLD_API_PRICE_URL, USD_EXCHANGE_RATE_URL
from app.schemas import MarketPricesResponse, MetalPriceResponse

TROY_OUNCE_GRAMS = 31.1034768
QUOTE_TIMEOUT_SECONDS = 15
USD_CNY_SYMBOL = "USD/CNY"


class MarketPriceFetchError(RuntimeError):
    """Raised when the external market quote source cannot be normalized."""


@dataclass(frozen=True)
class MetalQuote:
    symbol: str
    name: str
    currency: str
    price_usd_per_ounce: float
    updated_at: datetime | None


@dataclass(frozen=True)
class ExchangeRateQuote:
    rate: float
    updated_at: datetime | None


@dataclass(frozen=True)
class MetalQuoteConfig:
    metal: Literal["gold", "silver"]
    display_name: str
    symbol: Literal["XAU", "XAG"]


METAL_QUOTES: tuple[MetalQuoteConfig, ...] = (
    MetalQuoteConfig(metal="gold", display_name="国际黄金", symbol="XAU"),
    MetalQuoteConfig(metal="silver", display_name="国际白银", symbol="XAG"),
)


_HTTP_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "application/json",
}


def get_market_prices() -> MarketPricesResponse:
    fetched_at = datetime.now(timezone.utc)
    exchange_quote = _fetch_usd_cny_rate()
    if exchange_quote.rate <= 0:
        raise MarketPriceFetchError("USD/CNY exchange rate is not available.")

    prices = [
        _to_metal_response(config, _fetch_metal_quote(config.symbol), exchange_quote.rate, fetched_at)
        for config in METAL_QUOTES
    ]
    return MarketPricesResponse(
        prices=prices,
        exchange_rate_symbol=USD_CNY_SYMBOL,
        exchange_rate=round(exchange_quote.rate, 6),
        exchange_rate_time=exchange_quote.updated_at,
        fetched_at=fetched_at,
    )


def _to_metal_response(
    config: MetalQuoteConfig,
    quote_data: MetalQuote,
    usd_cny_rate: float,
    fetched_at: datetime,
) -> MetalPriceResponse:
    if quote_data.currency != "USD":
        raise MarketPriceFetchError(f"{quote_data.symbol} returned {quote_data.currency}, expected USD.")
    cny_per_ounce = quote_data.price_usd_per_ounce * usd_cny_rate
    return MetalPriceResponse(
        metal=config.metal,
        display_name=config.display_name,
        source_symbol=quote_data.symbol,
        source_name=f"Gold API {quote_data.name}",
        price_usd_per_ounce=round(quote_data.price_usd_per_ounce, 4),
        usd_cny_rate=round(usd_cny_rate, 6),
        price_cny_per_ounce=round(cny_per_ounce, 2),
        price_cny_per_gram=round(cny_per_ounce / TROY_OUNCE_GRAMS, 2),
        quote_time=quote_data.updated_at,
        fetched_at=fetched_at,
    )


def _fetch_metal_quote(symbol: Literal["XAU", "XAG"]) -> MetalQuote:
    payload = _get_json(GOLD_API_PRICE_URL.format(symbol=symbol), f"metal quote {symbol}")
    price = payload.get("price")
    currency = payload.get("currency")
    if not isinstance(price, (int, float)) or price <= 0:
        raise MarketPriceFetchError(f"Metal source returned invalid price for {symbol}.")
    if currency != "USD":
        raise MarketPriceFetchError(f"Metal source returned invalid currency for {symbol}.")
    return MetalQuote(
        symbol=str(payload.get("symbol") or symbol),
        name=str(payload.get("name") or symbol),
        currency=currency,
        price_usd_per_ounce=float(price),
        updated_at=_iso_to_datetime(payload.get("updatedAt")),
    )


def _fetch_usd_cny_rate() -> ExchangeRateQuote:
    payload = _get_json(USD_EXCHANGE_RATE_URL, "USD/CNY exchange rate")
    rates = payload.get("rates")
    if not isinstance(rates, dict):
        raise MarketPriceFetchError("Exchange-rate source returned no rates object.")
    rate = rates.get("CNY")
    if not isinstance(rate, (int, float)) or rate <= 0:
        raise MarketPriceFetchError("Exchange-rate source returned invalid USD/CNY rate.")
    return ExchangeRateQuote(rate=float(rate), updated_at=_timestamp_to_datetime(payload.get("time_last_update_unix")))


def _get_json(url: str, label: str) -> dict[str, Any]:
    try:
        response = httpx.get(url, headers=_HTTP_HEADERS, timeout=QUOTE_TIMEOUT_SECONDS, trust_env=False)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise MarketPriceFetchError(f"Failed to fetch {label}: {exc}") from exc
    except ValueError as exc:
        raise MarketPriceFetchError(f"Failed to parse {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise MarketPriceFetchError(f"{label} source returned invalid JSON payload.")
    return payload


def _iso_to_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _timestamp_to_datetime(value: Any) -> datetime | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)
