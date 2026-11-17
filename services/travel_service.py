import asyncio

from clients.countries_client import CountriesClient
from clients.rates_client import RatesClient


class TravelService:
    """Facade: combines both clients so a route needs a single call.

    The clients are passed in (dependency injection), so tests can hand in fakes.
    """

    def __init__(self, countries: CountriesClient, rates: RatesClient):
        self._countries = countries
        self._rates = rates

    async def get_country(self, name: str) -> dict:
        (country, currency), capital = await asyncio.gather(
            self._countries.get_currency(name), self._countries.get_capital(name)
        )
        return {"country": country, "currency": currency, "capital": capital}

    async def roam(self, name: str, budget_inr: float) -> dict:
        country, currency = await self._countries.get_currency(name)
        rate = 1.0 if currency == "INR" else await self._rates.get_rate("INR", currency)
        return {
            "country": country,
            "currency": currency,
            "rate": rate,
            "budget_inr": budget_inr,
            "budget_local": round(budget_inr * rate, 2),
        }
