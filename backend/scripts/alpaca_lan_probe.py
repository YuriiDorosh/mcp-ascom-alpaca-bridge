#!/usr/bin/env python3
"""Read-only probe: GET Alpaca HTTP management configureddevices using backend/.env.

This issues no slew/sync/tracking — only checks TCP + HTTP + JSON from the
Alpaca discovery/management surface (see README curl example).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

DEFAULT_TIMEOUT = 8.0


def _parse_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    raw = path.read_text(encoding="utf-8", errors="replace")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        env[key] = value
    return env


def build_management_devices_url(*, protocol: str, address: str) -> str:
    address = address.strip()
    if not address:
        raise ValueError("ALPACA_ADDRESS is empty")
    proto = (protocol or "http").strip().lower()
    if "://" in address:
        base = address.rstrip("/")
    else:
        base = f"{proto}://{address}".rstrip("/")
    return f"{base}/management/v1/configureddevices"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe Alpaca management API (GET configureddevices, read-only).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to backend .env (default: .env in cwd).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"HTTP timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    args = parser.parse_args()

    if not args.env_file.is_file():
        print(f"error: env file not found: {args.env_file}", file=sys.stderr)
        return 2

    file_env = _parse_dotenv(args.env_file)
    alpaca_address = os.environ.get("ALPACA_ADDRESS", file_env.get("ALPACA_ADDRESS", ""))
    alpaca_protocol = os.environ.get("ALPACA_PROTOCOL", file_env.get("ALPACA_PROTOCOL", "http"))

    try:
        url = build_management_devices_url(protocol=alpaca_protocol, address=alpaca_address)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"GET {url}")
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=args.timeout) as response:  # nosec B310 - local operator tool
            status = int(response.status)
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        print(f"error: HTTP {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"error: {exc.reason}", file=sys.stderr)
        print(
            "hint: check ALPACA_ADDRESS (host:port), device power, firewall; "
            "if the IP looks right but hangs, see README (stale ARP / DHCP reservation).",
            file=sys.stderr,
        )
        return 1

    if status != 200:
        print(f"error: unexpected HTTP status {status}", file=sys.stderr)
        return 1

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        print(f"error: response is not valid JSON: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2))
    print()
    print("OK: Alpaca management reachable (read-only; no mount commands sent).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
