"""`/telescopes/status` payload checks shared by operator tooling."""

from typing import Any


def assert_telescope_status_payload_matches_contract(payload: dict[str, Any]) -> None:
    """Raise AssertionError when JSON from GET /telescopes/status violates overlay rules."""

    assert "capabilities" in payload, "capabilities missing in telescope status"
    assert "connection_state" in payload, "connection_state missing in telescope status"
    assert "tracking_enabled" in payload, "tracking_enabled missing in telescope status"

    live = payload.get("alpaca_live")
    if not isinstance(live, dict):
        return

    cs = payload["connection_state"]
    te = payload["tracking_enabled"]
    reachable = live.get("reachable")
    connected = live.get("connected")
    tracking = live.get("tracking")

    if reachable is False:
        assert cs == "disconnected", (
            "connection_state must be disconnected when Alpaca probing reports an unreachable telescope server"
        )
        return

    if reachable is not True:
        return

    if connected is True:
        assert cs == "connected", "connection_state must be connected when alpaca_live shows a linked scope"
        if tracking is not None:
            assert te == tracking, "tracking_enabled must match alpaca_live.tracking when the driver reports it"
        return

    if connected is False:
        assert cs == "disconnected", (
            "connection_state must be disconnected when the Alpaca scope reports Connected=false while reachable"
        )
        assert te is False, "tracking_enabled must be false when the scope is reachable but not connected"
