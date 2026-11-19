import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger

from clients.countries_client import CountriesClient
from clients.rates_client import RatesClient
from config import settings
from db import get_session, init_db
from exceptions import NotFoundError, UpstreamUnavailableError
from logging_setup import setup_logging
from repositories.trip_repository import TripRepository
from schemas import TripCreate, TripOut, TripUpdate, TripWithBudgetOut
from services.trip_service import TripService
from services.travel_service import TravelService

setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Mini API Project", lifespan=lifespan)

countries_client = CountriesClient(settings.countries_api_url, settings.request_timeout_seconds)
rates_client = RatesClient(settings.frankfurter_api_url, settings.request_timeout_seconds)
service = TravelService(countries_client, rates_client)


def get_trip_service(session=Depends(get_session)) -> TripService:
    return TripService(TripRepository(session), countries_client, rates_client)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("{} {} -> unhandled error", request.method, request.url.path)
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("{} {} -> {} in {:.0f} ms", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


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


@app.post("/trips", response_model=TripOut, status_code=201)
async def create_trip(body: TripCreate, trips: TripService = Depends(get_trip_service)):
    return await trips.create(body)


@app.get("/trips", response_model=list[TripWithBudgetOut])
async def list_trips(trips: TripService = Depends(get_trip_service)):
    return await trips.list_with_budgets()


@app.get("/trips/{trip_id}", response_model=TripOut)
async def get_trip(trip_id: int, trips: TripService = Depends(get_trip_service)):
    return trips.get(trip_id)


@app.patch("/trips/{trip_id}", response_model=TripOut)
async def update_trip(trip_id: int, body: TripUpdate, trips: TripService = Depends(get_trip_service)):
    return await trips.update(trip_id, body)


@app.delete("/trips/{trip_id}", status_code=204)
async def delete_trip(trip_id: int, trips: TripService = Depends(get_trip_service)):
    trips.delete(trip_id)
    return Response(status_code=204)
