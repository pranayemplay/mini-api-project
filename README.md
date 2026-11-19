# Mini API Project

A small FastAPI app that answers travel-budget questions. It looks up a country's currency and capital (CountriesNow) and converts a budget in INR into the local currency using today's rate (Frankfurter). It also saves planned trips in a Postgres database. No API keys are needed.

## Requirements

- Python 3.12 or newer
- Docker Desktop (to run it with Docker Compose, or to get a Postgres for running it locally)

## Run it locally

```bash
git clone <your-repo-url>
cd mini-api-project
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
docker compose up -d db          # just the database; the app runs on your laptop
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API page. The app needs a running Postgres, and `DATABASE_URL` in `.env` (host `localhost`) points at the one Compose starts.

## Run it with Docker Compose

```bash
cp .env.example .env             # first time only; change the password if you like
docker compose up --build
```

This builds the app image and starts two services: `db` (Postgres 17) and `app`. The app waits until Postgres reports healthy before it starts. Then open http://localhost:8000/docs.

| Command | What it does |
|---|---|
| `docker compose up --build` | Build and start both services (add `-d` to run in the background) |
| `docker compose ps` | Show what is running, and whether `db` is healthy |
| `docker compose logs -f app` | Follow the app's logs |
| `docker compose down` | Stop both services. Your trips stay in the `pgdata` volume |
| `docker compose down -v` | Stop both **and delete the data**, so you start with an empty database |

Postgres reads its username, password and database name only when it first creates the volume. If you change them in `.env` later, run `docker compose down -v` first.

## Configuration

Settings are read from environment variables (loaded from `.env`). The app refuses to start if a required one is missing.

| Name | Controls | Example / default |
|---|---|---|
| `COUNTRIES_API_URL` | Base URL of CountriesNow | `https://countriesnow.space/api/v0.1/countries` |
| `FRANKFURTER_API_URL` | Base URL of Frankfurter | `https://api.frankfurter.dev/v2` |
| `REQUEST_TIMEOUT_SECONDS` | Max seconds to wait for an outside API | `5` (default) |
| `DATABASE_URL` | Where the app finds Postgres (required) | `postgresql+psycopg://mini_api:change-me@localhost:5432/mini_api` |
| `LOG_LEVEL` | How much the app logs | `INFO` (default); `DEBUG`, `WARNING`, `ERROR` also work |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | The database Compose creates. Read by `docker-compose.yml`, not by the app | `mini_api` / `change-me` / `mini_api` |

Under Compose, `docker-compose.yml` builds the app's `DATABASE_URL` from the three `POSTGRES_*` values and uses the host `db` (the service name) instead of `localhost`. The `localhost` value in `.env` is for running `uvicorn` on your laptop. Keep the password free of characters such as `@ : / ? #`, because it sits inside a URL.

In `.env`, write plain `NAME=value` lines with no quotes or trailing comments. `.env` is never committed or copied into the image.

## Endpoints

### `GET /health`
```json
{"status": "ok"}
```

### `GET /countries/{name}`
`GET /countries/japan`
```json
{"country": "Japan", "currency": "JPY", "capital": "Tokyo"}
```

### `GET /roam/{name}?budget_inr=`
`GET /roam/japan?budget_inr=150000`
```json
{"country": "Japan", "currency": "JPY", "rate": 1.8, "budget_inr": 150000.0, "budget_local": 270000.0}
```
(The numbers above are illustrative; the real rate changes daily.)

### Trips

A trip is a planned visit: who is going, where, how much they can spend (in INR) and when. You send `traveller`, `country`, `budget_inr` and `travel_date`; the API adds `id`, `currency_code` (looked up from CountriesNow) and `created_at`. The country is stored under the name CountriesNow uses, so `japan` is saved as `Japan`.

#### `POST /trips` → 201
```json
{"traveller": "Asha", "country": "japan", "budget_inr": 150000, "travel_date": "2026-12-20"}
```
```json
{"id": 1, "traveller": "Asha", "country": "Japan", "currency_code": "JPY", "budget_inr": 150000.0,
 "travel_date": "2026-12-20", "created_at": "2026-11-17T10:42:00.123456Z"}
```

#### `GET /trips` → 200
Every trip, with its budget converted at today's rate (one rate lookup per currency, however many trips use it).
```json
[{"id": 1, "traveller": "Asha", "country": "Japan", "currency_code": "JPY", "budget_inr": 150000.0,
  "travel_date": "2026-12-20", "created_at": "2026-11-17T10:42:00.123456Z",
  "rate": 1.8, "budget_local": 270000.0}]
```
(The rate is illustrative; the real one changes daily.)

#### `GET /trips/{id}` → 200
Same body as `POST /trips`, without `rate` and `budget_local`.

#### `PATCH /trips/{id}` → 200
Send only the fields to change. If `country` changes, its currency is looked up again.
```json
{"budget_inr": 175000}
```
Returns the updated trip.

#### `DELETE /trips/{id}` → 204
No body.

### Errors

| Case | Status | Example |
|---|---|---|
| Country doesn't exist | 404 | `GET /countries/Atlantis` → `{"detail": "Country 'Atlantis' not found."}` |
| Country doesn't exist when saving a trip | 404 | `POST /trips` with `"country": "Atlantis"` |
| Trip id doesn't exist (GET, PATCH, DELETE) | 404 | `GET /trips/99999` → `{"detail": "Trip 99999 not found."}` |
| An outside API is down or too slow | 503 | `{"detail": "Countries API is unavailable or too slow."}` |
| Budget is zero or negative | 422 | `GET /roam/japan?budget_inr=0`, or `"budget_inr": 0` in a trip |
| Travel date is in the past (today is fine) | 422 | `"travel_date": "2020-01-01"` → message says the date is in the past |
| A required field is missing, or a value has the wrong type | 422 | `POST /trips` without `country`; `GET /trips/abc` |
| `PATCH` sends `null` for a field | 422 | Leave a field out to keep it; `null` is not allowed |

A 422 comes from validation and is returned before any outside API or the database is touched.

## Logging

The app logs to the console, one line per event, at `LOG_LEVEL`. Docker collects it: `docker compose logs -f app`.

```
2026-11-17 10:42:01 | INFO | GET /trips -> 200 in 412 ms
2026-11-17 10:42:01 | INFO | Frankfurter GET /rate/INR/JPY -> 200 in 188 ms
2026-11-17 10:42:09 | WARNING | CountriesNow GET /currency/q -> timeout after 5000 ms
```

Every request to the app and every call to CountriesNow or Frankfurter gets a line with its status and latency. Failed outside calls are logged as warnings with the reason. Passwords and the database URL are never logged.

## Project structure

```
main.py                      Routes and request logging only; turns our errors into 404 / 503
config.py                    Settings read from .env
exceptions.py                NotFoundError, TripNotFoundError, UpstreamUnavailableError
db.py                        Database engine, the trips table, one session per request
schemas.py                   Pydantic models for trips (validation and responses)
logging_setup.py             loguru configuration
clients/
  countries_client.py        Adapter for CountriesNow
  rates_client.py            Adapter for Frankfurter
repositories/
  trip_repository.py         All database access for trips
services/
  travel_service.py          Facade over both clients
  trip_service.py            Trips: currency lookup, storage, conversion
docker-compose.yml           The app and Postgres, started together
Dockerfile                   Builds the app image
.dockerignore                Keeps .env, .venv, .git out of the image
requirements.txt             Pinned packages
.env.example                 Template for .env
postman/                     Exported Postman collection and environment
```

## Design notes

- **Adapter:** `CountriesClient` and `RatesClient` each hide one public API (its URLs and response shape) behind methods that return plain Python values. They are the only files that import `httpx`.
- **Facade:** `TravelService` combines both clients so each route is a single call.
- **Dependency injection:** the service receives its clients when created, so a fake client can be passed in for tests (single responsibility and dependency inversion from SOLID).
- **Errors:** clients raise our own exceptions; only `main.py` knows about HTTP status codes.
- **Repository:** `TripRepository` is the only place that runs queries against the `trips` table (together with `db.py`, the only code that imports SQLAlchemy). It hands back plain `Trip` objects and returns `None` for a missing trip. It has no idea what a 404 is, and it never calls an outside API. That keeps SQL in one spot, lets `TripService` be tested with a fake repository, and means a change of database touches one file.
- **Service layer:** `TripService` gets the repository and both clients when it is created. It looks up currencies, raises `TripNotFoundError`, and converts budgets. `main.py` stays routes only.
- **Sessions:** each request gets its own database session through a FastAPI dependency, closed when the request ends.
- **Money:** budgets are `Decimal` in Python and `numeric(12, 2)` in Postgres, never float.
- **Tables:** created at startup with `create_all`. A migration tool such as Alembic is the next step when the schema needs to change.
