"""
ScanSearch CLI — query the ScanSearch API from your terminal.

Examples:
    scansearch search "port:9200 country:DE"
    scansearch ip 1.1.1.1
    scansearch scan 192.0.2.0/24 --ports 22,80,443
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from . import __version__
from .client import Client
from .exceptions import ScanSearchError


def _print_json(data: Any) -> None:
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False, default=str)
    sys.stdout.write("\n")


def cmd_search(api: Client, args) -> int:
    res = api.search(args.query, page=args.page, per_page=args.per_page,
                     country=args.country, port=args.port, service=args.service)
    _print_json(res)
    return 0


def cmd_ip(api: Client, args) -> int:
    _print_json(api.ip(args.ip))
    return 0


def cmd_scan(api: Client, args) -> int:
    job = api.scan(
        targets=args.targets,
        ports=args.ports,
        modules=args.modules.split(",") if args.modules else ["ports"],
        speed=args.speed,
    )
    print(f"Scan started: task_id={job.get('task_id')}", file=sys.stderr)
    if args.wait:
        final = api.scan_wait(job["task_id"], poll_interval=5.0, timeout=args.timeout)
        _print_json(final)
    else:
        _print_json(job)
    return 0


def cmd_status(api: Client, args) -> int:
    _print_json(api.scan_status(args.task_id))
    return 0


def cmd_stop(api: Client, args) -> int:
    _print_json(api.scan_stop(args.task_id))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="scansearch",
        description="ScanSearch CLI — live internet scanning & exposure research.",
        epilog="API key required. Get one: https://scansearch.net/dashboard/api-keys/",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--api-key", default=os.environ.get("SCANSEARCH_API_KEY", ""),
                        help="API key (env: SCANSEARCH_API_KEY).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="Run a search query.")
    p_search.add_argument("query")
    p_search.add_argument("--page", type=int, default=1)
    p_search.add_argument("--per-page", type=int, default=20)
    p_search.add_argument("--country")
    p_search.add_argument("--port", type=int)
    p_search.add_argument("--service")
    p_search.set_defaults(func=cmd_search)

    p_ip = sub.add_parser("ip", help="Look up a single IP.")
    p_ip.add_argument("ip")
    p_ip.set_defaults(func=cmd_ip)

    p_scan = sub.add_parser("scan", help="Launch a live scan.")
    p_scan.add_argument("targets", nargs="+", help="One or more CIDR / IP / domain targets.")
    p_scan.add_argument("--ports", default="1-1000")
    p_scan.add_argument("--modules", default="ports", help='"ports" or "ports,services"')
    p_scan.add_argument("--speed", type=int, help="kpps override")
    p_scan.add_argument("--wait", action="store_true", help="Block until scan finishes.")
    p_scan.add_argument("--timeout", type=int, default=1800)
    p_scan.set_defaults(func=cmd_scan)

    p_status = sub.add_parser("status", help="Check scan status.")
    p_status.add_argument("task_id", type=int)
    p_status.set_defaults(func=cmd_status)

    p_stop = sub.add_parser("stop", help="Stop a running scan.")
    p_stop.add_argument("task_id", type=int)
    p_stop.set_defaults(func=cmd_stop)

    args = parser.parse_args(argv)

    if not args.api_key:
        parser.error("Missing API key. Pass --api-key or set SCANSEARCH_API_KEY.")

    try:
        api = Client(api_key=args.api_key)
        return args.func(api, args)
    except ScanSearchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
