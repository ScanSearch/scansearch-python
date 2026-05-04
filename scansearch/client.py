"""
ScanSearch API client — on-demand internet scans via REST API.

Usage:
    from scansearch import Client

    api = Client("YOUR_API_KEY")
    job = api.scan(targets=["192.0.2.0/24"], ports="22,80,443", modules=["ports", "services"])
    result = api.scan_wait(job["task_id"])
    print(result["open_ports_found"])
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

from .exceptions import APIError, AuthError, NotFoundError, RateLimitError


DEFAULT_BASE_URL = "https://scansearch.net/api/v1"
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = "scansearch-python/0.1.0 (+https://github.com/ScanSearch/scansearch-python)"


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

    # -------------------------------------------------------------------- scan

    def scan(
        self,
        targets: List[str],
        ports: str = "1-1000",
        modules: Optional[List[str]] = None,
        speed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Launch a live SYN+service scan of one or more targets.

        Args:
            targets: List of CIDRs, IPs, country codes (``"country:DE"``), or domains.
                Examples:
                    ``["192.0.2.0/24"]``
                    ``["10.0.0.0/8", "203.0.113.5"]``
                    ``["country:DE"]`` — whole country
                    ``["example.com"]`` — domain (resolved to IPs server-side)
            ports: Port spec — single ``"80"``, list ``"22,80,443"``, range ``"1-65535"``.
            modules: ``["ports"]`` (default) or ``["ports", "services"]`` for service detection.
                Optional extras: ``"subdomains"``, ``"screenshots"``, ``"technologies"``.
            speed: Scan speed in kpps (packets-per-second × 1000). Defaults to your
                plan's scanner_speed. Free tier is capped at ``2`` kpps; paid plans
                range ``100`` (entry) — ``10000`` (high-throughput) kpps.

        Returns ``{"task_id": int, "status": "pending" | "queued"}``.

        Use :meth:`scan_status` to poll, :meth:`scan_wait` to block until done.
        """
        payload: Dict[str, Any] = {
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

        Args:
            task_id: Scan task id returned by :meth:`scan`.
            poll_interval: Seconds between status polls.
            timeout: Total wait deadline (raises :class:`TimeoutError` after).

        Returns the final status dict — open_ports_found, services_found,
        progress_stage, etc.
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
