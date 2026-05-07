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


def test_assert_mcp_bootstrap_requires_hardware_overview_contract():
    payload = {
        "hardware_smoke_plan": {
            "trigger_task_id": "P5-HW-SMOKE",
        },
        "hardware_validation_plan": {
            "trigger_task_id": "P5-HW-VALIDATION",
        },
        "hardware_overview": {
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
        },
    }
    runner._assert_mcp_bootstrap(payload)


def test_assert_mcp_bootstrap_rejects_trigger_mismatch_between_top_level_and_overview(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(runner, "_assert_hardware_overview", lambda _payload: None)
    payload = {
        "hardware_smoke_plan": {
            "trigger_task_id": "P5-HW-SMOKE",
        },
        "hardware_validation_plan": {
            "trigger_task_id": "P5-HW-VALIDATION",
        },
        "hardware_overview": {
            "readiness": {
                "schema_version": "v1",
                "trigger_task_id": "P5-HW-SMOKE",
                "requires_real_telescope_now": False,
            },
            "smoke_plan": {
                "schema_version": "v1",
                "trigger_task_id": "P5-HW-WRONG",
                "steps": [{"step": 1, "action": "x", "expected_result": "y"}],
            },
            "validation_plan": {
                "schema_version": "v1",
                "trigger_task_id": "P5-HW-VALIDATION",
                "steps": [{"step": 1, "action": "x", "expected_result": "y"}],
            },
        },
    }
    with pytest.raises(AssertionError, match="bootstrap smoke/overview trigger mismatch"):
        runner._assert_mcp_bootstrap(payload)


def test_assert_mcp_execution_plan_requires_hardware_overview_contract():
    payload = {
        "hardware_smoke_plan": {
            "trigger_task_id": "P5-HW-SMOKE",
        },
        "hardware_validation_plan": {
            "trigger_task_id": "P5-HW-VALIDATION",
        },
        "hardware_overview": {
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
        },
        "steps": [{"step": 1, "tool_name": "telescope.get_status"}],
    }
    runner._assert_mcp_execution_plan(payload)


def test_assert_mcp_execution_plan_rejects_trigger_mismatch_between_top_level_and_overview(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(runner, "_assert_hardware_overview", lambda _payload: None)
    payload = {
        "hardware_smoke_plan": {
            "trigger_task_id": "P5-HW-SMOKE",
        },
        "hardware_validation_plan": {
            "trigger_task_id": "P5-HW-VALIDATION",
        },
        "hardware_overview": {
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
                "trigger_task_id": "P5-HW-WRONG",
                "steps": [{"step": 1, "action": "x", "expected_result": "y"}],
            },
        },
        "steps": [{"step": 1, "tool_name": "telescope.get_status"}],
    }
    with pytest.raises(AssertionError, match="execution validation/overview trigger mismatch"):
        runner._assert_mcp_execution_plan(payload)


def test_write_notes_includes_summary_and_follow_up(tmp_path: Path):
    notes_path = tmp_path / "notes.md"
    results = [
        runner.CheckResult(
            name="hardware.readiness",
            method="GET",
            url="http://localhost/readiness",
            ok=True,
            status_code=200,
            error=None,
            details=None,
        ),
        runner.CheckResult(
            name="mcp.bootstrap",
            method="GET",
            url="http://localhost/bootstrap",
            ok=False,
            status_code=None,
            error="assertion_failed: mismatch",
            details=None,
        ),
    ]

    runner._write_notes(notes_path, results, "http://127.0.0.1:8000")
    content = notes_path.read_text(encoding="utf-8")
    assert "# Hardware Preflight Notes" in content
    assert "- Total checks: 2" in content
    assert "- Failed: 1" in content
    assert "`mcp.bootstrap`" in content
    assert "Investigate failed checks before starting `P5-HW-SMOKE`." in content


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
        allow_command_checks_when_not_ready=False,
        command_token="",
        strict=True,
        notes_path="",
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


def test_main_writes_notes_when_notes_path_is_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    args = Namespace(
        base_url="http://127.0.0.1:8000",
        report_path=str(tmp_path / "report.json"),
        validation_only=False,
        include_commands=False,
        allow_command_checks_when_not_ready=False,
        command_token="",
        strict=False,
        notes_path=str(tmp_path / "notes.md"),
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)

    ok = runner.CheckResult(
        name="ok",
        method="GET",
        url="http://ok",
        ok=True,
        status_code=200,
        error=None,
        details=None,
    )
    queue = [ok, ok, ok, ok, ok, ok, ok, ok, ok]
    monkeypatch.setattr(runner, "_run_check", lambda **_kwargs: queue.pop(0))
    monkeypatch.setattr(runner, "_write_report", lambda *_args, **_kwargs: None)

    called = {"notes": False}

    def fake_write_notes(*_args, **_kwargs):
        called["notes"] = True

    monkeypatch.setattr(runner, "_write_notes", fake_write_notes)

    exit_code = runner.main()
    assert exit_code == 0
    assert called["notes"] is True


def test_main_blocks_command_checks_when_readiness_is_not_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    args = Namespace(
        base_url="http://127.0.0.1:8000",
        report_path=str(tmp_path / "report.json"),
        validation_only=False,
        include_commands=True,
        allow_command_checks_when_not_ready=False,
        command_token="",
        strict=False,
        notes_path="",
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)

    readiness_ok = runner.CheckResult(
        name="hardware.readiness",
        method="GET",
        url="http://ready",
        ok=True,
        status_code=200,
        error=None,
        details={"payload": {"requires_real_telescope_now": False}},
    )
    ok = runner.CheckResult(
        name="ok",
        method="GET",
        url="http://ok",
        ok=True,
        status_code=200,
        error=None,
        details=None,
    )
    queue = [readiness_ok, ok, ok, ok, ok, ok, ok, ok, ok]
    calls = {"count": 0}

    def fake_run_check(**_kwargs):
        calls["count"] += 1
        return queue.pop(0)

    monkeypatch.setattr(runner, "_run_check", fake_run_check)
    monkeypatch.setattr(runner, "_write_report", lambda *_args, **_kwargs: None)

    exit_code = runner.main()
    assert exit_code == 0
    assert calls["count"] == 9


def test_main_allows_command_checks_with_override_when_not_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    args = Namespace(
        base_url="http://127.0.0.1:8000",
        report_path=str(tmp_path / "report.json"),
        validation_only=False,
        include_commands=True,
        allow_command_checks_when_not_ready=True,
        command_token="",
        strict=False,
        notes_path="",
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)

    readiness_ok = runner.CheckResult(
        name="hardware.readiness",
        method="GET",
        url="http://ready",
        ok=True,
        status_code=200,
        error=None,
        details={"payload": {"requires_real_telescope_now": False}},
    )
    ok = runner.CheckResult(
        name="ok",
        method="GET",
        url="http://ok",
        ok=True,
        status_code=200,
        error=None,
        details=None,
    )
    queue = [readiness_ok, ok, ok, ok, ok, ok, ok, ok, ok, ok, ok, ok]
    calls = {"count": 0}

    def fake_run_check(**_kwargs):
        calls["count"] += 1
        return queue.pop(0)

    monkeypatch.setattr(runner, "_run_check", fake_run_check)
    monkeypatch.setattr(runner, "_write_report", lambda *_args, **_kwargs: None)

    exit_code = runner.main()
    assert exit_code == 0
    assert calls["count"] == 12
