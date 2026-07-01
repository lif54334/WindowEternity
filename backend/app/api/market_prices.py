from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import MarketPricesResponse
from app.services.market_prices import MarketPriceFetchError, get_market_prices

router = APIRouter(prefix="/api/market-prices", tags=["market-prices"])


@router.get("", response_model=MarketPricesResponse)
def read_market_prices() -> MarketPricesResponse:
    try:
        return get_market_prices()
    except MarketPriceFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
