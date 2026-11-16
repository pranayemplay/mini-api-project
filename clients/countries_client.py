import httpx

from exceptions import NotFoundError, UpstreamUnavailableError


class CountriesClient:
    """Adapter for CountriesNow: hides its URLs and response shape."""

    def __init__(self, base_url: str, timeout: float):
        self._base_url = base_url
        self._timeout = httpx.Timeout(timeout)

    async def _lookup(self, field: str, country: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._base_url}/{field}/q", params={"country": country})
            body = resp.json()
        except (httpx.RequestError, ValueError):
            raise UpstreamUnavailableError("Countries API is unavailable or too slow.")
        if resp.status_code >= 500 or resp.status_code == 429:
            raise UpstreamUnavailableError("Countries API is unavailable.")
        if resp.status_code != 200 or not isinstance(body, dict) or body.get("error") or not body.get("data"):
            raise NotFoundError(f"Country '{country}' not found.")
        return body["data"]

    async def get_currency(self, country: str) -> tuple[str, str]:
        """Return (country name, currency code)."""
        data = await self._lookup("currency", country)
        code = data.get("currency")
        if not code:
            raise NotFoundError(f"No currency found for '{country}'.")
        return data.get("name", country), code

    async def get_capital(self, country: str) -> str | None:
        data = await self._lookup("capital", country)
        return data.get("capital")
