import pytest

from domain.ports.alpaca_client import (
    AlpacaLiveSnapshot,
    IAlpacaTelescopeClient,
)
from logic.commands.telescope_control import (
    SetTelescopeTrackingCommand,
    SetTelescopeTrackingCommandHandler,
    SlewToIcrsCommand,
    SlewToIcrsCommandHandler,
    SyncMountToIcrsCommand,
    SyncMountToIcrsCommandHandler,
)
from logic.mediator.base import Mediator


class RecordingTelescopePort(IAlpacaTelescopeClient):
    """Fake Alpaca telescope for dispatch checks (no Alpaca RPC)."""

    def __init__(self) -> None:
        self.slew_calls: list[tuple[float, float]] = []
        self.sync_calls: list[tuple[float, float]] = []
        self.tracking_calls: list[bool] = []

    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        return None

    async def slew_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self.slew_calls.append((ra_hours, dec_degrees))

    async def sync_mount_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self.sync_calls.append((ra_hours, dec_degrees))

    async def set_tracking_enabled(self, enabled: bool) -> None:
        self.tracking_calls.append(enabled)


@pytest.mark.asyncio
async def test_command_handlers_invoke_alpaca_port():
    port = RecordingTelescopePort()
    mediator = Mediator()

    slew_h = SlewToIcrsCommandHandler(_mediator=mediator, alpaca_telescope=port)
    sync_h = SyncMountToIcrsCommandHandler(_mediator=mediator, alpaca_telescope=port)
    track_h = SetTelescopeTrackingCommandHandler(_mediator=mediator, alpaca_telescope=port)

    assert await slew_h.handle(SlewToIcrsCommand(ra_hours=5.5, dec_degrees=10.25)) == {'status': 'ok'}
    assert await sync_h.handle(SyncMountToIcrsCommand(ra_hours=5.5, dec_degrees=10.25)) == {'status': 'ok'}
    assert await track_h.handle(SetTelescopeTrackingCommand(enabled=True)) == {'status': 'ok'}

    assert port.slew_calls == [(5.5, 10.25)]
    assert port.sync_calls == [(5.5, 10.25)]
    assert port.tracking_calls == [True]
