import sys
import types

import pytest

from domain.exceptions.telescope import AlpacaDriverException
from infra.integrations.alpaca.telescope_client import AlpycaTelescopeClient


class StubConfig:
    alpaca_enabled = True
    alpaca_address = '127.0.0.1:11111'
    alpaca_device_number = 0
    alpaca_protocol = 'http'
    alpaca_connect_timeout_seconds = 0.2


def _install_fake_telescope_module(monkeypatch, telescope_cls):
    module = types.ModuleType('alpaca.telescope')
    module.Telescope = telescope_cls
    monkeypatch.setitem(sys.modules, 'alpaca.telescope', module)


class FakeTelescopeOk:
    last_instance = None
    all_slew_calls: list[tuple[float, float]] = []
    all_sync_calls: list[tuple[float, float]] = []

    def __init__(self, address, device_number, protocol='http'):
        self.address = address
        self.device_number = device_number
        self.protocol = protocol
        self.Connecting = False
        self.Connected = False
        self.Tracking = False
        self.CanSlew = True
        self.CanSync = True
        self.Name = 'Mock Scope'
        self.Description = 'Mock Desc'
        self.slew_calls = []
        self.sync_calls = []
        FakeTelescopeOk.last_instance = self

    def Connect(self):
        self.Connected = True

    def SlewToCoordinates(self, ra, dec):
        self.slew_calls.append((ra, dec))
        FakeTelescopeOk.all_slew_calls.append((ra, dec))

    def SyncToCoordinates(self, ra, dec):
        self.sync_calls.append((ra, dec))
        FakeTelescopeOk.all_sync_calls.append((ra, dec))


class FakeTelescopeNoSync(FakeTelescopeOk):
    def __init__(self, address, device_number, protocol='http'):
        super().__init__(address, device_number, protocol=protocol)
        self.CanSync = False


class DisabledConfig(StubConfig):
    alpaca_enabled = False


@pytest.mark.asyncio
async def test_alpyca_snapshot_and_commands_with_mocked_driver(monkeypatch):
    FakeTelescopeOk.all_slew_calls.clear()
    FakeTelescopeOk.all_sync_calls.clear()
    _install_fake_telescope_module(monkeypatch, FakeTelescopeOk)
    client = AlpycaTelescopeClient(config=StubConfig())

    snapshot = await client.read_live_telescope_snapshot()
    assert snapshot is not None
    assert snapshot.reachable is True
    assert snapshot.connected is True
    assert snapshot.device_name == 'Mock Scope'

    await client.slew_to_icrs(5.5, -1.2)
    await client.sync_mount_to_icrs(5.5, -1.2)
    await client.set_tracking_enabled(True)

    instance = FakeTelescopeOk.last_instance
    assert instance is not None
    assert instance.address == '127.0.0.1:11111'
    assert FakeTelescopeOk.all_slew_calls == [(5.5, -1.2)]
    assert FakeTelescopeOk.all_sync_calls == [(5.5, -1.2)]
    assert instance.Tracking is True


@pytest.mark.asyncio
async def test_alpyca_control_disabled_without_hardware(monkeypatch):
    _install_fake_telescope_module(monkeypatch, FakeTelescopeOk)
    client = AlpycaTelescopeClient(config=DisabledConfig())

    assert await client.read_live_telescope_snapshot() is None

    with pytest.raises(AlpacaDriverException):
        await client.slew_to_icrs(1.0, 2.0)


@pytest.mark.asyncio
async def test_alpyca_sync_capability_failure_maps_to_domain_exception(monkeypatch):
    _install_fake_telescope_module(monkeypatch, FakeTelescopeNoSync)
    client = AlpycaTelescopeClient(config=StubConfig())

    with pytest.raises(AlpacaDriverException) as exc:
        await client.sync_mount_to_icrs(1.0, 2.0)

    assert 'CanSync=False' in exc.value.message
