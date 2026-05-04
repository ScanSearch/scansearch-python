"""
ScanSearch CLI — launch on-demand internet scans from your terminal.

Examples:
    scansearch scan 192.0.2.0/24 --ports 22,80,443 --wait
    scansearch scan country:DE --ports 9200 --speed 1000 --wait
    scansearch status 1234
    scansearch stop 1234
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
        description="ScanSearch CLI — on-demand internet scanner.",
        epilog="API key required. Get one: https://scansearch.net/dashboard/api-keys/",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--api-key", default=os.environ.get("SCANSEARCH_API_KEY", ""),
                        help="API key (env: SCANSEARCH_API_KEY).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Launch a live scan.")
    p_scan.add_argument("targets", nargs="+",
                        help="One or more CIDR / IP / country:CC / domain targets.")
    p_scan.add_argument("--ports", default="1-1000",
                        help='Port spec: "22,80,443" or "1-65535".')
    p_scan.add_argument("--modules", default="ports",
                        help='Comma list: "ports" or "ports,services".')
    p_scan.add_argument("--speed", type=int, help="Scan speed in kpps (overrides plan default).")
    p_scan.add_argument("--wait", action="store_true", help="Block until scan finishes.")
    p_scan.add_argument("--timeout", type=int, default=1800,
                        help="Wait deadline in seconds when --wait (default 1800).")
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
