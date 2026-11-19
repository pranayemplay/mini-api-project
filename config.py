"""All settings live here. Nothing else in the app hardcodes a URL or a timeout."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # reads .env if it exists; real environment variables (e.g. Docker's) still work

_LOG_LEVELS = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}


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


def _log_level(name: str, default: str) -> str:
    value = (os.getenv(name) or default).upper()
    if value not in _LOG_LEVELS:
        raise RuntimeError(f"Setting {name} must be one of {sorted(_LOG_LEVELS)}, got {value!r}.")
    return value


@dataclass(frozen=True)
class Settings:
    countries_api_url: str
    frankfurter_api_url: str
    request_timeout_seconds: float
    database_url: str
    log_level: str


settings = Settings(
    countries_api_url=_required("COUNTRIES_API_URL"),
    frankfurter_api_url=_required("FRANKFURTER_API_URL"),
    request_timeout_seconds=_timeout("REQUEST_TIMEOUT_SECONDS", 5.0),
    database_url=_required("DATABASE_URL"),
    log_level=_log_level("LOG_LEVEL", "INFO"),
)
