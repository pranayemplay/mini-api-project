"""All settings live here. Nothing else in the app hardcodes a URL or a timeout."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # reads .env if it exists; real environment variables (e.g. Docker's) still work


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required setting {name}. Set it in .env (see .env.example).")
    return value.rstrip("/")


def _timeout(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        raise RuntimeError(f"Setting {name} must be a number of seconds, got {raw!r}.")


@dataclass(frozen=True)
class Settings:
    countries_api_url: str
    frankfurter_api_url: str
    request_timeout_seconds: float


settings = Settings(
    countries_api_url=_required("COUNTRIES_API_URL"),
    frankfurter_api_url=_required("FRANKFURTER_API_URL"),
    request_timeout_seconds=_timeout("REQUEST_TIMEOUT_SECONDS", 5.0),
)
