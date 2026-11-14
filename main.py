import asyncio

import httpx
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Mini API Project")

COUNTRIES_URL = "https://countriesnow.space/api/v0.1/countries"
FRANKFURTER_URL = "https://api.frankfurter.dev/v2"
TIMEOUT = httpx.Timeout(5.0)  # a slow API can't hang the app


async def get_json(url: str, params: dict | None = None) -> tuple[int, dict]:
    """GET a URL. Down, slow, or non-JSON upstream -> 503."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
        body = resp.json()
    except (httpx.RequestError, ValueError):
        raise HTTPException(503, "An upstream API is unavailable or too slow. Try again later.")
    return resp.status_code, body if isinstance(body, dict) else {}


async def countries_now(field: str, name: str) -> dict:
    """Look up currency or capital for a country; 404 if it doesn't exist."""
    status, body = await get_json(f"{COUNTRIES_URL}/{field}/q", {"country": name})
    if status >= 500 or status == 429:
        raise HTTPException(503, "Countries API is unavailable.") 
    if status != 200 or body.get("error") or not body.get("data"):
        raise HTTPException(404, f"Country '{name}' not found.")
    return body["data"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/countries/{name}")
async def get_country(name: str):
    currency_data, capital_data = await asyncio.gather(
        countries_now("currency", name), countries_now("capital", name)
    )
    return {
        "country": currency_data.get("name", name),
        "currency": currency_data.get("currency"),
        "capital": capital_data.get("capital"),
    }


@app.get("/roam/{name}")
async def roam(name: str, budget_inr: float = Query(..., gt=0)):
    data = await countries_now("currency", name)
    currency = data.get("currency")
    if not currency:
        raise HTTPException(404, f"No currency found for '{name}'.")

    if currency == "INR":
        rate = 1.0
    else:
        status, body = await get_json(f"{FRANKFURTER_URL}/rate/INR/{currency}")
        if status >= 500 or status == 429:
            raise HTTPException(503, "Exchange rate API is unavailable.")
        if status != 200 or "rate" not in body:
            raise HTTPException(404, f"No exchange rate available for INR to {currency}.")
        rate = body["rate"]

    return {
        "country": data.get("name", name),
        "currency": currency,
        "rate": rate,
        "budget_inr": budget_inr,
        "budget_local": round(budget_inr * rate, 2),
    }