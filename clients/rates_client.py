import time

import httpx
from loguru import logger

from exceptions import NotFoundError, UpstreamUnavailableError


class RatesClient:
    """Adapter for Frankfurter: hides its URLs and response shape."""

    def __init__(self, base_url: str, timeout: float):
        self._base_url = base_url
        self._timeout = httpx.Timeout(timeout)

    async def get_rate(self, base: str, quote: str) -> float:
        path = f"/rate/{base}/{quote}"
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}{path}")
        except httpx.TimeoutException:
            logger.warning("Frankfurter GET {} -> timeout after {:.0f} ms", path, _ms(started))
            raise UpstreamUnavailableError("Exchange rate API is unavailable or too slow.")
        except httpx.RequestError as exc:
            logger.warning("Frankfurter GET {} -> request failed ({}) after {:.0f} ms", path, type(exc).__name__, _ms(started))
            raise UpstreamUnavailableError("Exchange rate API is unavailable or too slow.")

        level = "WARNING" if resp.status_code >= 500 or resp.status_code == 429 else "INFO"
        logger.log(level, "Frankfurter GET {} -> {} in {:.0f} ms", path, resp.status_code, _ms(started))

        try:
            body = resp.json()
        except ValueError:
            logger.warning("Frankfurter GET {} -> response was not valid JSON", path)
            raise UpstreamUnavailableError("Exchange rate API is unavailable or too slow.")
        if resp.status_code >= 500 or resp.status_code == 429:
            raise UpstreamUnavailableError("Exchange rate API is unavailable.")
        if resp.status_code != 200 or not isinstance(body, dict) or "rate" not in body:
            raise NotFoundError(f"No exchange rate available for {base} to {quote}.")
        return body["rate"]


def _ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
