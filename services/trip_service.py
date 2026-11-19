import asyncio
from decimal import ROUND_HALF_UP, Decimal

from clients.countries_client import CountriesClient
from clients.rates_client import RatesClient
from exceptions import TripNotFoundError
from repositories.trip_repository import Trip, TripRepository
from schemas import TripCreate, TripUpdate

_CENT = Decimal("0.01")


class TripService:
    """Trips: looks up the currency, stores trips through the repository, converts budgets.

    The repository and both clients are passed in, the same way TravelService gets its clients.
    It writes no SQL and never touches a database session.
    """

    def __init__(self, repository: TripRepository, countries: CountriesClient, rates: RatesClient):
        self._repo = repository
        self._countries = countries
        self._rates = rates

    async def create(self, data: TripCreate) -> Trip:
        country, currency = await self._countries.get_currency(data.country)
        return self._repo.add(
            traveller=data.traveller,
            country=country,
            currency_code=currency,
            budget_inr=data.budget_inr,
            travel_date=data.travel_date,
        )

    async def list_with_budgets(self) -> list[dict]:
        trips = self._repo.list()
        # One rate per currency, however many trips use it.
        currencies = sorted({trip.currency_code for trip in trips})
        fetched = await asyncio.gather(*(self._rate_for(code) for code in currencies))
        rates = dict(zip(currencies, fetched))
        return [
            {
                **vars(trip),
                "rate": rates[trip.currency_code],
                "budget_local": _convert(trip.budget_inr, rates[trip.currency_code]),
            }
            for trip in trips
        ]

    def get(self, trip_id: int) -> Trip:
        trip = self._repo.get(trip_id)
        if trip is None:
            raise TripNotFoundError(trip_id)
        return trip

    async def update(self, trip_id: int, data: TripUpdate) -> Trip:
        self.get(trip_id)  # 404 before any outside call if the trip doesn't exist
        fields = data.model_dump(exclude_unset=True)
        if "country" in fields:  # the country changed, so its currency may have too
            fields["country"], fields["currency_code"] = await self._countries.get_currency(fields["country"])
        trip = self._repo.update(trip_id, **fields)
        if trip is None:  # deleted between the check above and the update
            raise TripNotFoundError(trip_id)
        return trip

    def delete(self, trip_id: int) -> None:
        if not self._repo.delete(trip_id):
            raise TripNotFoundError(trip_id)

    async def _rate_for(self, currency: str) -> float:
        return 1.0 if currency == "INR" else await self._rates.get_rate("INR", currency)


def _convert(budget_inr: Decimal, rate: float) -> Decimal:
    return (budget_inr * Decimal(str(rate))).quantize(_CENT, rounding=ROUND_HALF_UP)
