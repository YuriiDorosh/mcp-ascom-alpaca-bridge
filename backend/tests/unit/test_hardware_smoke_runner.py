from argparse import Namespace
import importlib.util
from pathlib import Path
import sys

import pytest


RUNNER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "hardware_smoke_runner.py"
_SPEC = importlib.util.spec_from_file_location("hardware_smoke_runner", RUNNER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
runner = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = runner
_SPEC.loader.exec_module(runner)


def test_assert_readiness_accepts_v1_contract():
    payload = {
        "schema_version": "v1",
        "trigger_task_id": "P5-HW-SMOKE",
        "requires_real_telescope_now": False,
    }
    runner._assert_readiness(payload)


def test_assert_smoke_plan_requires_step_fields():
    payload = {
        "schema_version": "v1",
        "trigger_task_id": "P5-HW-SMOKE",
        "steps": [{"step": 1, "action": "x", "expected_result": "y"}],
    }
    runner._assert_smoke_plan(payload)

    with pytest.raises(AssertionError):
        runner._assert_smoke_plan(
            {
                "schema_version": "v1",
                "trigger_task_id": "P5-HW-SMOKE",
                "steps": [{"step": 1, "action": "x"}],
            }
        )


def test_assert_validation_plan_accepts_expected_contract():
    payload = {
        "schema_version": "v1",
        "trigger_task_id": "P5-HW-VALIDATION",
        "steps": [{"step": 1, "action": "x", "expected_result": "y"}],
    }
    runner._assert_validation_plan(payload)


def test_assert_hardware_overview_accepts_aggregated_contract():
    payload = {
        "readiness": {
            "schema_version": "v1",
            "trigger_task_id": "P5-HW-SMOKE",
            "requires_real_telescope_now": False,
        },
        "smoke_plan": {
            "schema_version": "v1",
            "trigger_task_id": "P5-HW-SMOKE",
            "steps": [{"step": 1, "action": "x", "expected_result": "y"}],
        },
        "validation_plan": {
            "schema_version": "v1",
            "trigger_task_id": "P5-HW-VALIDATION",
            "steps": [{"step": 1, "action": "x", "expected_result": "y"}],
        },
    }
    runner._assert_hardware_overview(payload)


def test_run_check_reports_assertion_failure(monkeypatch: pytest.MonkeyPatch):
    def fake_http_json(**_kwargs):
        return 200, {"bad": "payload"}

    monkeypatch.setattr(runner, "_http_json", fake_http_json)
    def failing_validator(payload):
        assert "required" in payload, "missing key"

    result = runner._run_check(
        name="broken-check",
        method="GET",
        url="http://localhost/check",
        validator=failing_validator,
    )
    assert result.ok is False
    assert result.error is not None
    assert result.error.startswith("assertion_failed:")


def test_main_returns_nonzero_on_strict_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    args = Namespace(
        base_url="http://127.0.0.1:8000",
        report_path=str(tmp_path / "report.json"),
        validation_only=False,
        include_commands=False,
        command_token="",
        strict=True,
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)

    first_ok = runner.CheckResult(
        name="ok",
        method="GET",
        url="http://ok",
        ok=True,
        status_code=200,
        error=None,
        details=None,
    )
    failed = runner.CheckResult(
        name="fail",
        method="GET",
        url="http://fail",
        ok=False,
        status_code=503,
        error="http_error: unavailable",
        details=None,
    )
    queue = [first_ok, first_ok, first_ok, first_ok, first_ok, first_ok, first_ok, first_ok, failed]
    monkeypatch.setattr(runner, "_run_check", lambda **_kwargs: queue.pop(0))
    monkeypatch.setattr(runner, "_write_report", lambda *_args, **_kwargs: None)

    exit_code = runner.main()
    assert exit_code == 1
