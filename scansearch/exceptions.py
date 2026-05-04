"""ScanSearch SDK exception hierarchy."""


class ScanSearchError(Exception):
    """Base exception for all SDK errors."""


class AuthError(ScanSearchError):
    """Raised on 401 — missing, invalid, or revoked API key."""


class RateLimitError(ScanSearchError):
    """Raised on 429 — daily quota or per-minute rate limit exceeded."""


class NotFoundError(ScanSearchError):
    """Raised on 404 — resource not found (IP, scan task, etc.)."""


class APIError(ScanSearchError):
    """Raised on other 4xx/5xx responses. ``status`` and ``body`` are attached."""

    def __init__(self, status: int, body: str = ""):
        self.status = status
        self.body = body
        super().__init__(f"ScanSearch API error {status}: {body[:200]}")
