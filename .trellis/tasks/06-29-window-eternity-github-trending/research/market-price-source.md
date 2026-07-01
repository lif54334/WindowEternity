# Market price source research

## Scope

The new market-prices module needs current international gold and silver prices converted to CNY for display in the Window of Eternity portal.

## Verified live endpoints

Verified on 2026-06-30 from the backend Python virtualenv:

- `https://api.gold-api.com/price/XAU` returns JSON for gold with `currency=USD`, `price`, `symbol=XAU`, and `updatedAt`.
- `https://api.gold-api.com/price/XAG` returns JSON for silver with `currency=USD`, `price`, `symbol=XAG`, and `updatedAt`.
- `https://open.er-api.com/v6/latest/USD` returns JSON with `rates.CNY` and `time_last_update_unix`.

Rejected source during research:

- Yahoo Finance chart endpoint returned usable data from PowerShell, but the backend `httpx` runtime received 403 responses when connecting directly and TLS/proxy errors when inheriting environment proxy settings. It should not be the backend source for this implementation.

## Implementation decision

Use Gold API for metal USD-per-troy-ounce quotes and open.er-api for USD/CNY. Keep both calls inside `backend/app/services/market_prices.py` and return source timestamps, backend fetch timestamp, USD price, USD/CNY, CNY per troy ounce, and CNY per gram.

The UI should label the source clearly and must expose refresh failures instead of showing stale fake values.

## Validation

Network checks require explicit network access. Source-level validation can still run with:

```powershell
python -m compileall backend/app
cd frontend
npm.cmd run build
```
