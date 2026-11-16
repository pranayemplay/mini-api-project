import httpx

from exceptions import NotFoundError, UpstreamUnavailableError


class RatesClient:
    """Adapter for Frankfurter: hides its URLs and response shape."""

    def __init__(self, base_url: str, timeout: float):
        self._base_url = base_url
        self._timeout = httpx.Timeout(timeout)

    async def get_rate(self, base: str, quote: str) -> float:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}/rate/{base}/{quote}")
            body = resp.json()
        except (httpx.RequestError, ValueError):
            raise UpstreamUnavailableError("Exchange rate API is unavailable or too slow.")
        if resp.status_code >= 500 or resp.status_code == 429:
            raise UpstreamUnavailableError("Exchange rate API is unavailable.")
        if resp.status_code != 200 or not isinstance(body, dict) or "rate" not in body:
            raise NotFoundError(f"No exchange rate available for {base} to {quote}.")
        return body["rate"]

