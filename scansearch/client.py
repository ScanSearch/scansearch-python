"""
ScanSearch API client.

Usage:
    from scansearch import Client

    api = Client("YOUR_API_KEY")
    res = api.search("port:9200 country:DE", per_page=50)
    for hit in res["results"]:
        print(hit["ip"], hit["ports"])
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterator, List, Optional

import requests

from .exceptions import APIError, AuthError, NotFoundError, RateLimitError


DEFAULT_BASE_URL = "https://scansearch.net/api/v1"
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = "scansearch-python/0.1.0 (+https://github.com/scansearch/scansearch-python)"


class Client:
    """
    Thin wrapper around the ScanSearch REST API.

    Args:
        api_key: 64-char API key from https://scansearch.net/dashboard/api-keys/
                 If omitted, falls back to the ``SCANSEARCH_API_KEY`` env var.
        base_url: Override the API base URL (rarely needed).
        timeout: Per-request timeout in seconds.
        session: Optional pre-built ``requests.Session`` (e.g. with retries).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or os.environ.get("SCANSEARCH_API_KEY", "")
        if not self.api_key:
            raise AuthError(
                "No API key provided. Pass api_key= or set SCANSEARCH_API_KEY. "
                "Get one at https://scansearch.net/dashboard/api-keys/"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
        })

    # ------------------------------------------------------------------ search

    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        country: Optional[str] = None,
        port: Optional[int] = None,
        service: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run a search query against ScanSearch.

        Query syntax:
            - ``"1.2.3.4"``        — single IP
            - ``"1.2.3.0/24"``     — CIDR
            - ``"port:9200"``      — by port
            - ``"service:http"``   — by service/protocol
            - ``"country:DE"``     — by country code
            - ``"asn:15169"``      — by ASN number
            - ``"org:google"``     — by organisation name (substring)
            - ``"any free text"``  — full-text on banners/titles/vendor

        Returns the raw API response dict — ``results``, ``total``, ``page``, etc.
        """
        params: Dict[str, Any] = {"q": query, "page": page, "per_page": per_page}
        if country:
            params["country"] = country
        if port is not None:
            params["port"] = port
        if service:
            params["service"] = service
        return self._get("/search/", params=params)

    def search_iter(self, query: str, per_page: int = 100, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Yield every result for a query, handling pagination automatically.

        Stops at API quota — wrap in try/except :class:`RateLimitError`.
        """
        page = 1
        while True:
            data = self.search(query, page=page, per_page=per_page, **kwargs)
            results = data.get("results") or []
            for hit in results:
                yield hit
            if len(results) < per_page:
                return
            page += 1

    def search_filters(self) -> Dict[str, Any]:
        """Return available filter values (countries, top ports, top services)."""
        return self._get("/search/filters/")

    def ip(self, ip: str) -> Dict[str, Any]:
        """Fetch full intelligence record for a single IP."""
        return self._get(f"/search/ip/{ip}/")

    # -------------------------------------------------------------------- scan

    def scan(
        self,
        targets: List[str],
        ports: str = "1-1000",
        modules: Optional[List[str]] = None,
        speed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Launch a live scan of one or more CIDR / IP / domain targets.

        Args:
            targets: List of CIDRs, IPs, or domains (e.g. ``["1.2.3.0/24"]``).
            ports: Port spec, e.g. ``"22,80,443"`` or ``"1-65535"``.
            modules: ``["ports"]`` (default) or ``["ports", "services"]``.
            speed: kpps override. Defaults to your plan's scanner_speed.

        Returns ``{"task_id": int, "status": "pending"}``.
        Use :meth:`scan_status` to poll, :meth:`scan_wait` to block until done.
        """
        payload = {
            "targets": targets,
            "ports": ports,
            "modules": modules or ["ports"],
        }
        if speed is not None:
            payload["speed"] = speed
        return self._post("/scan/", json=payload)

    def scan_status(self, task_id: int) -> Dict[str, Any]:
        """Get the current status, progress and partial results of a scan."""
        return self._get(f"/scan/{task_id}/status/")

    def scan_stop(self, task_id: int) -> Dict[str, Any]:
        """Force-stop a running scan and finalise partial results."""
        return self._post(f"/scan/{task_id}/stop/")

    def scan_wait(self, task_id: int, poll_interval: float = 5.0, timeout: float = 1800) -> Dict[str, Any]:
        """
        Block until a scan reaches a terminal status (completed/stopped/failed).

        Returns the final status dict.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            data = self.scan_status(task_id)
            if data.get("status") in ("completed", "stopped", "failed", "cancelled"):
                return data
            time.sleep(poll_interval)
        raise TimeoutError(f"Scan {task_id} did not finish within {timeout}s")

    # ------------------------------------------------------------------ helper

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("POST", path, json=json)

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = self.base_url + path
        try:
            resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as e:
            raise APIError(0, str(e)) from e

        if resp.status_code == 401:
            raise AuthError(resp.text or "Unauthorized")
        if resp.status_code == 404:
            raise NotFoundError(resp.text or "Not found")
        if resp.status_code == 429:
            raise RateLimitError(resp.text or "Rate limit exceeded")
        if not resp.ok:
            raise APIError(resp.status_code, resp.text)

        try:
            return resp.json()
        except ValueError:
            raise APIError(resp.status_code, "Non-JSON response")
