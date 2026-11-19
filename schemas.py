"""Pydantic models for trips. FastAPI checks every request body against them and returns a 422
before any of our code runs, so bad data never reaches the database."""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

# Money is a Decimal inside the app; in JSON responses it is a plain number, as in /roam.
JsonNumber = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


def _not_in_the_past(value: date | None) -> date | None:
    if value is not None and value < date.today():
        raise ValueError(f"travel_date {value.isoformat()} is in the past")
    return value


def _not_null(value):
    if value is None:
        raise ValueError("must not be null; leave the field out to keep its current value")
    return value


class TripCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    traveller: str = Field(min_length=1)
    country: str = Field(min_length=1)
    budget_inr: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    travel_date: date

    @field_validator("travel_date")
    @classmethod
    def travel_date_not_in_past(cls, value: date) -> date:
        return _not_in_the_past(value)


class TripUpdate(BaseModel):
    """Every field is optional: only the fields that are sent change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    traveller: str | None = Field(default=None, min_length=1)
    country: str | None = Field(default=None, min_length=1)
    budget_inr: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    travel_date: date | None = None

    @field_validator("traveller", "country", "budget_inr", "travel_date")
    @classmethod
    def sent_fields_not_null(cls, value):
        return _not_null(value)

    @field_validator("travel_date")
    @classmethod
    def travel_date_not_in_past(cls, value: date) -> date:
        return _not_in_the_past(value)


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    traveller: str
    country: str
    currency_code: str
    budget_inr: JsonNumber
    travel_date: date
    created_at: datetime


class TripWithBudgetOut(TripOut):
    """A trip in the list: also shows the budget at today's rate."""

    rate: float
    budget_local: JsonNumber
