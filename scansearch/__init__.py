"""
ScanSearch Python SDK — official client for the ScanSearch API.

ScanSearch is a live internet scanning and exposure-research platform — a
fresh-data alternative to Shodan and Censys. Get an API key at
https://scansearch.net/dashboard/api-keys/
"""

from .client import Client
from .exceptions import (
    ScanSearchError,
    AuthError,
    RateLimitError,
    NotFoundError,
    APIError,
)

__version__ = "0.1.0"
__all__ = [
    "Client",
    "ScanSearchError",
    "AuthError",
    "RateLimitError",
    "NotFoundError",
    "APIError",
]
