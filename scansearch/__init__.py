"""
ScanSearch Python SDK — official client for the ScanSearch API.

ScanSearch is an on-demand internet scanner. Trigger a live SYN+service scan
of any IP, CIDR, country or domain through the REST API and get fresh results
in seconds. Get an API key at https://scansearch.net/dashboard/api-keys/
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
