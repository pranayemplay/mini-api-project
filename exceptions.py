"""The app's own errors. Clients raise them; main.py turns them into HTTP status codes."""


class NotFoundError(Exception):
    """The country (or a rate for it) doesn't exist. Becomes a 404."""


class UpstreamUnavailableError(Exception):
    """An outside API is down, too slow, or returned something unusable. Becomes a 503."""
