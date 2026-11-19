"""The app's own errors. Clients and services raise them; main.py turns them into HTTP status codes."""


class NotFoundError(Exception):
    """The country (or a rate for it) doesn't exist. Becomes a 404."""


class TripNotFoundError(NotFoundError):
    """No trip has this id. Also a 404, through the NotFoundError handler."""

    def __init__(self, trip_id: int):
        super().__init__(f"Trip {trip_id} not found.")
        self.trip_id = trip_id


class UpstreamUnavailableError(Exception):
    """An outside API is down, too slow, or returned something unusable. Becomes a 503."""
