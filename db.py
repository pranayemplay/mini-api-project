"""Database setup: the engine, the trips table, and one session per request.

Together with repositories/trip_repository.py, this is the only code that imports SQLAlchemy.
"""
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, Numeric, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class TripRow(Base):
    __tablename__ = "trips"
    __table_args__ = (CheckConstraint("budget_inr > 0", name="ck_trips_budget_positive"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    traveller: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    budget_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def init_db() -> None:
    """Create the tables if they don't exist yet. (Migrations such as Alembic come later.)"""
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, closed when the request ends."""
    with SessionLocal() as session:
        yield session
