# Mini API Project

A small FastAPI app that answers travel-budget questions. It looks up a country's currency and capital (CountriesNow) and converts a budget in INR into the local currency using today's rate (Frankfurter). No API keys are needed.

## Requirements

- Python 3.12 or newer
- Docker Desktop (only if you want to run it in Docker)

## Run it locally

```bash
git clone <your-repo-url>
cd mini-api-project
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API page.

## Run it with Docker

```bash
docker build -t mini-api-project .
docker run --rm -p 8000:8000 --env-file .env mini-api-project
```

Then open http://localhost:8000/docs. Press Ctrl+C to stop. The `.env` file is not copied into the image, so `--env-file .env` is required.

## Configuration

Settings are read from environment variables (loaded from `.env`). The app refuses to start if a URL is missing.

| Name | Controls | Example / default |
|---|---|---|
| `COUNTRIES_API_URL` | Base URL of CountriesNow | `https://countriesnow.space/api/v0.1/countries` |
| `FRANKFURTER_API_URL` | Base URL of Frankfurter | `https://api.frankfurter.dev/v2` |
| `REQUEST_TIMEOUT_SECONDS` | Max seconds to wait for an outside API | `5` (default) |

In `.env`, write plain `NAME=value` lines with no quotes or trailing comments (Docker's `--env-file` keeps them).

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

### Errors

| Case | Status | Example |
|---|---|---|
| Country doesn't exist | 404 | `GET /countries/Atlantis` → `{"detail": "Country 'Atlantis' not found."}` |
| An outside API is down or too slow | 503 | `{"detail": "Countries API is unavailable or too slow."}` |
| Budget is zero or negative | 422 | `GET /roam/japan?budget_inr=0` |

## Project structure

```
main.py                      Routes only; turns our errors into 404 / 503
config.py                    Settings read from .env
exceptions.py                NotFoundError, UpstreamUnavailableError
clients/
  countries_client.py        Adapter for CountriesNow
  rates_client.py            Adapter for Frankfurter
services/
  travel_service.py          Facade over both clients
Dockerfile                   Builds the image
.dockerignore                Keeps .env, .venv, .git out of the image
requirements.txt             Pinned packages
.env.example                 Template for .env
postman/                     Exported Postman collection
```

## Design notes

- **Adapter:** `CountriesClient` and `RatesClient` each hide one public API (its URLs and response shape) behind methods that return plain Python values. They are the only files that import `httpx`.
- **Facade:** `TravelService` combines both clients so each route is a single call.
- **Dependency injection:** the service receives its clients when created, so a fake client can be passed in for tests (single responsibility and dependency inversion from SOLID).
- **Errors:** clients raise our own exceptions; only `main.py` knows about HTTP status codes.
