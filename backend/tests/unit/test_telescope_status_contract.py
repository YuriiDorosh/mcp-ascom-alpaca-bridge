import sys
from pathlib import Path

import pytest


_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))
from telescope_status_contract import (
    assert_telescope_status_payload_matches_contract,
)


def test_telescope_status_contract_requires_tracking_enabled_field():
    base = {"capabilities": {}, "connection_state": "disconnected"}
    with pytest.raises(AssertionError):
        assert_telescope_status_payload_matches_contract(base)

    assert_telescope_status_payload_matches_contract({**base, "tracking_enabled": False})


def test_telescope_status_contract_skips_live_rules_when_alpaca_live_null():
    assert_telescope_status_payload_matches_contract(
        {
            "capabilities": {},
            "connection_state": "wormhole",
            "tracking_enabled": True,
            "alpaca_live": None,
        }
    )


def test_telescope_status_contract_enforces_unreachable_alpaca_overlay():
    assert_telescope_status_payload_matches_contract(
        {
            "capabilities": {},
            "connection_state": "disconnected",
            "tracking_enabled": True,
            "alpaca_live": {"reachable": False, "connected": None, "error_hint": "timeout"},
        },
    )
    with pytest.raises(AssertionError):
        assert_telescope_status_payload_matches_contract(
            {
                "capabilities": {},
                "connection_state": "connected",
                "tracking_enabled": True,
                "alpaca_live": {"reachable": False},
            },
        )


def test_telescope_status_contract_enforces_connected_scope_overlay():
    assert_telescope_status_payload_matches_contract(
        {
            "capabilities": {},
            "connection_state": "connected",
            "tracking_enabled": False,
            "alpaca_live": {"reachable": True, "connected": True, "tracking": False},
        },
    )
    with pytest.raises(AssertionError):
        assert_telescope_status_payload_matches_contract(
            {
                "capabilities": {},
                "connection_state": "disconnected",
                "tracking_enabled": False,
                "alpaca_live": {"reachable": True, "connected": True, "tracking": False},
            },
        )


def test_telescope_status_contract_tracking_must_mirror_alpaca_when_reported():
    with pytest.raises(AssertionError):
        assert_telescope_status_payload_matches_contract(
            {
                "capabilities": {},
                "connection_state": "connected",
                "tracking_enabled": False,
                "alpaca_live": {"reachable": True, "connected": True, "tracking": True},
            },
        )


def test_telescope_status_contract_enforces_disconnected_while_reachable_but_not_linked():
    assert_telescope_status_payload_matches_contract(
        {
            "capabilities": {},
            "connection_state": "disconnected",
            "tracking_enabled": False,
            "alpaca_live": {"reachable": True, "connected": False, "tracking": None},
        },
    )
    with pytest.raises(AssertionError):
        assert_telescope_status_payload_matches_contract(
            {
                "capabilities": {},
                "connection_state": "disconnected",
                "tracking_enabled": True,
                "alpaca_live": {"reachable": True, "connected": False, "tracking": None},
            },
        )
