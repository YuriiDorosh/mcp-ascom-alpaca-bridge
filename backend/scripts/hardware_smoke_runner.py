#!/usr/bin/env python3
"""Run hardware preflight checks against Alpaca Astro Center API.

This runner is safe by default:
- It verifies readiness plus smoke/validation contracts.
- It executes only read-only checks unless --include-commands is explicitly set.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Callable
from urllib import error
from urllib import request


@dataclass
class CheckResult:
    name: str
    method: str
    url: str
    ok: bool
    status_code: int | None
    error: str | None
    details: dict[str, Any] | None


def _http_json(method: str, url: str, body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request_headers = {"Accept": "application/json"}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)

    req = request.Request(url=url, data=payload, method=method, headers=request_headers)
    with request.urlopen(req, timeout=20) as response:  # nosec B310 - local operator tool
        status_code = int(response.status)
        raw = response.read().decode("utf-8")
        return status_code, json.loads(raw)


def _run_check(
    *,
    name: str,
    method: str,
    url: str,
    validator: Callable[[Any], None],
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> CheckResult:
    try:
        status_code, payload = _http_json(method=method, url=url, body=body, headers=headers)
        validator(payload)
        return CheckResult(
            name=name,
            method=method,
            url=url,
            ok=True,
            status_code=status_code,
            error=None,
            details=None,
        )
    except AssertionError as exc:
        return CheckResult(
            name=name,
            method=method,
            url=url,
            ok=False,
            status_code=None,
            error=f"assertion_failed: {exc}",
            details=None,
        )
    except error.HTTPError as exc:
        return CheckResult(
            name=name,
            method=method,
            url=url,
            ok=False,
            status_code=int(exc.code),
            error=f"http_error: {exc.reason}",
            details=None,
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            name=name,
            method=method,
            url=url,
            ok=False,
            status_code=None,
            error=f"exception: {exc}",
            details=None,
        )


def _assert_readiness(payload: dict[str, Any]) -> None:
    assert payload["schema_version"] == "v1", "schema_version must be v1"
    assert payload["trigger_task_id"] == "P5-HW-SMOKE", "trigger_task_id must be P5-HW-SMOKE"
    assert "requires_real_telescope_now" in payload, "requires_real_telescope_now missing"


def _assert_smoke_plan(payload: dict[str, Any]) -> None:
    assert payload["schema_version"] == "v1", "schema_version must be v1"
    assert payload["trigger_task_id"] == "P5-HW-SMOKE", "trigger_task_id must be P5-HW-SMOKE"
    steps = payload["steps"]
    assert isinstance(steps, list) and len(steps) >= 1, "steps must be non-empty list"
    first = steps[0]
    assert all(key in first for key in ("step", "action", "expected_result")), "first step fields missing"


def _assert_validation_plan(payload: dict[str, Any]) -> None:
    assert payload["schema_version"] == "v1", "schema_version must be v1"
    assert payload["trigger_task_id"] == "P5-HW-VALIDATION", "trigger_task_id must be P5-HW-VALIDATION"
    steps = payload["steps"]
    assert isinstance(steps, list) and len(steps) >= 1, "steps must be non-empty list"
    first = steps[0]
    assert all(key in first for key in ("step", "action", "expected_result")), "first step fields missing"


def _assert_hardware_overview(payload: dict[str, Any]) -> None:
    readiness = payload["readiness"]
    smoke_plan = payload["smoke_plan"]
    validation_plan = payload["validation_plan"]

    _assert_readiness(readiness)
    _assert_smoke_plan(smoke_plan)
    _assert_validation_plan(validation_plan)


def _assert_mcp_bootstrap(payload: dict[str, Any]) -> None:
    smoke_plan = payload["hardware_smoke_plan"]
    validation_plan = payload["hardware_validation_plan"]
    overview = payload["hardware_overview"]
    assert smoke_plan["trigger_task_id"] == "P5-HW-SMOKE", "bootstrap smoke trigger mismatch"
    assert validation_plan["trigger_task_id"] == "P5-HW-VALIDATION", "bootstrap validation trigger mismatch"
    _assert_hardware_overview(overview)
    assert overview["smoke_plan"]["trigger_task_id"] == smoke_plan["trigger_task_id"], "bootstrap smoke/overview trigger mismatch"
    assert overview["validation_plan"]["trigger_task_id"] == validation_plan["trigger_task_id"], "bootstrap validation/overview trigger mismatch"


def _assert_mcp_execution_plan(payload: dict[str, Any]) -> None:
    smoke_plan = payload["hardware_smoke_plan"]
    validation_plan = payload["hardware_validation_plan"]
    overview = payload["hardware_overview"]
    assert smoke_plan["trigger_task_id"] == "P5-HW-SMOKE", "execution smoke trigger mismatch"
    assert validation_plan["trigger_task_id"] == "P5-HW-VALIDATION", "execution validation trigger mismatch"
    _assert_hardware_overview(overview)
    assert overview["smoke_plan"]["trigger_task_id"] == smoke_plan["trigger_task_id"], "execution smoke/overview trigger mismatch"
    assert overview["validation_plan"]["trigger_task_id"] == validation_plan["trigger_task_id"], "execution validation/overview trigger mismatch"
    assert isinstance(payload["steps"], list) and len(payload["steps"]) >= 1, "execution steps must be non-empty"


def _assert_status(payload: dict[str, Any]) -> None:
    assert "capabilities" in payload, "capabilities missing in telescope status"
    assert "connection_state" in payload, "connection_state missing in telescope status"


def _assert_capabilities(payload: dict[str, Any]) -> None:
    assert "supports_slew" in payload, "supports_slew missing"
    assert "supports_sync" in payload, "supports_sync missing"
    assert "supports_tracking" in payload, "supports_tracking missing"


def _assert_audit(payload: Any) -> None:
    assert isinstance(payload, list), "audit response must be a list"


def _assert_command_ack(payload: dict[str, Any]) -> None:
    assert payload.get("status") == "ok", "command endpoint did not return status=ok"


def _write_report(path: Path, results: list[CheckResult], base_url: str) -> None:
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "summary": {
            "total_checks": len(results),
            "passed_checks": sum(1 for item in results if item.ok),
            "failed_checks": sum(1 for item in results if not item.ok),
        },
        "checks": [asdict(item) for item in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _write_notes(path: Path, results: list[CheckResult], base_url: str) -> None:
    failed = [item for item in results if not item.ok]
    lines = [
        "# Hardware Preflight Notes",
        "",
        f"- Generated (UTC): {datetime.now(UTC).isoformat()}",
        f"- Base URL: `{base_url}`",
        f"- Total checks: {len(results)}",
        f"- Passed: {len(results) - len(failed)}",
        f"- Failed: {len(failed)}",
        "",
        "## Check Results",
    ]
    for item in results:
        status = "PASS" if item.ok else "FAIL"
        status_code = f" (status={item.status_code})" if item.status_code is not None else ""
        lines.append(f"- [{status}] `{item.name}`{status_code}")
        if item.error:
            lines.append(f"  - error: `{item.error}`")

    if failed:
        lines.extend(
            [
                "",
                "## Follow-up",
                "- Investigate failed checks before starting `P5-HW-SMOKE`.",
            ],
        )
    else:
        lines.extend(
            [
                "",
                "## Follow-up",
                "- Dry-run preflight is green; keep this note for operator traceability.",
            ],
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run P5 hardware preflight checks against local API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL.")
    parser.add_argument(
        "--report-path",
        default="artifacts/hardware-smoke-dry-run.json",
        help="Output path for JSON report.",
    )
    parser.add_argument(
        "--validation-only",
        action="store_true",
        help="Focus on P5-HW-VALIDATION checks and skip direct smoke-plan endpoint.",
    )
    parser.add_argument(
        "--include-commands",
        action="store_true",
        help="Include movement command checks (POST /commands/*). Use only when telescope is intentionally connected.",
    )
    parser.add_argument(
        "--command-token",
        default="",
        help="Optional command auth token for command endpoints.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero exit code when any check fails.",
    )
    parser.add_argument(
        "--notes-path",
        default="",
        help="Optional output path for markdown operator notes generated from check results.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    results: list[CheckResult] = []

    checks = [
        ("hardware.readiness", "GET", f"{base_url}/telescopes/hardware/readiness", _assert_readiness, None, None),
        (
            "hardware.validation_plan",
            "GET",
            f"{base_url}/telescopes/hardware/validation-plan",
            _assert_validation_plan,
            None,
            None,
        ),
        (
            "hardware.overview",
            "GET",
            f"{base_url}/telescopes/hardware/overview",
            _assert_hardware_overview,
            None,
            None,
        ),
        ("mcp.bootstrap", "GET", f"{base_url}/telescopes/tools/mcp-bootstrap", _assert_mcp_bootstrap, None, None),
        ("mcp.execution_plan", "GET", f"{base_url}/telescopes/tools/mcp-execution-plan", _assert_mcp_execution_plan, None, None),
        ("telescope.status", "GET", f"{base_url}/telescopes/status", _assert_status, None, None),
        ("telescope.capabilities", "GET", f"{base_url}/telescopes/capabilities", _assert_capabilities, None, None),
        ("telescope.command_audit", "GET", f"{base_url}/telescopes/commands/audit?limit=10", _assert_audit, None, None),
    ]
    if args.validation_only is False:
        checks.insert(1, ("hardware.smoke_plan", "GET", f"{base_url}/telescopes/hardware/smoke-plan", _assert_smoke_plan, None, None))

    for name, method, url, validator, body, headers in checks:
        results.append(_run_check(name=name, method=method, url=url, validator=validator, body=body, headers=headers))

    if args.include_commands:
        token_headers = {}
        if args.command_token:
            token_headers["X-Command-Token"] = args.command_token

        command_checks = [
            (
                "telescope.command.slew_icrs",
                "POST",
                f"{base_url}/telescopes/commands/slew-icrs",
                _assert_command_ack,
                {"ra_hours": 1.0, "dec_degrees": 5.0},
                token_headers,
            ),
            (
                "telescope.command.sync_icrs",
                "POST",
                f"{base_url}/telescopes/commands/sync-icrs",
                _assert_command_ack,
                {"ra_hours": 1.0, "dec_degrees": 5.0},
                token_headers,
            ),
            (
                "telescope.command.set_tracking",
                "POST",
                f"{base_url}/telescopes/commands/tracking",
                _assert_command_ack,
                {"enabled": True},
                token_headers,
            ),
        ]
        for name, method, url, validator, body, headers in command_checks:
            results.append(_run_check(name=name, method=method, url=url, validator=validator, body=body, headers=headers))

    _write_report(Path(args.report_path), results, base_url)
    if args.notes_path:
        _write_notes(Path(args.notes_path), results, base_url)

    failed = [item for item in results if not item.ok]
    for item in results:
        marker = "PASS" if item.ok else "FAIL"
        status_chunk = f" status={item.status_code}" if item.status_code is not None else ""
        error_chunk = f" error={item.error}" if item.error else ""
        print(f"[{marker}] {item.name}{status_chunk}{error_chunk}")

    print(f"\nReport written to: {args.report_path}")
    print(f"Checks: total={len(results)} passed={len(results) - len(failed)} failed={len(failed)}")
    if failed and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
