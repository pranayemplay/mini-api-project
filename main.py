from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from clients.countries_client import CountriesClient
from clients.rates_client import RatesClient
from config import settings
from exceptions import NotFoundError, UpstreamUnavailableError
from services.travel_service import TravelService

app = FastAPI(title="Mini API Project")

service = TravelService(
    CountriesClient(settings.countries_api_url, settings.request_timeout_seconds),
    RatesClient(settings.frankfurter_api_url, settings.request_timeout_seconds),
)


@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UpstreamUnavailableError)
async def unavailable_handler(request, exc: UpstreamUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/countries/{name}")
async def get_country(name: str):
    return await service.get_country(name)


@app.get("/roam/{name}")
async def roam(name: str, budget_inr: float = Query(..., gt=0)):
    return await service.roam(name, budget_inr)
