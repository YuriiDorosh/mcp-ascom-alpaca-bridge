import pytest

from domain.entities.telescope import Telescope
from domain.ports.alpaca_client import (
    AlpacaLiveSnapshot,
    IAlpacaClient,
)
from infra.repositories.telescope.base import BaseTelescopeRepository
from logic.queries.telescope import (
    GetTelescopeStatusQuery,
    GetTelescopeStatusQueryHandler,
)


class FakeRepo(BaseTelescopeRepository):
    def __init__(self, telescope: Telescope | None = None):
        self._scope = telescope or Telescope()

    async def get_primary(self) -> Telescope:
        return self._scope

    async def save_primary(self, telescope: Telescope) -> Telescope:
        return telescope


class FakeAlpacaClient(IAlpacaClient):
    def __init__(self, snapshot: AlpacaLiveSnapshot | None):
        self.snapshot = snapshot

    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        return self.snapshot


@pytest.mark.asyncio
async def test_status_query_exposes_live_capabilities_when_available():
    handler = GetTelescopeStatusQueryHandler(
        telescope_repository=FakeRepo(),
        alpaca_client=FakeAlpacaClient(
            AlpacaLiveSnapshot(
                reachable=True,
                connected=True,
                tracking=True,
                supports_slew=True,
                supports_sync=False,
                supports_tracking=True,
                device_name='Mock',
            ),
        ),
    )

    payload = await handler.handle(GetTelescopeStatusQuery())

    assert payload['capabilities'] == {
        'supports_slew': True,
        'supports_sync': False,
        'supports_tracking': True,
        'source': 'alpaca-live',
    }


@pytest.mark.asyncio
async def test_status_query_defaults_capabilities_when_alpaca_disabled():
    handler = GetTelescopeStatusQueryHandler(
        telescope_repository=FakeRepo(),
        alpaca_client=FakeAlpacaClient(None),
    )

    payload = await handler.handle(GetTelescopeStatusQuery())

    assert payload['capabilities'] == {
        'supports_slew': False,
        'supports_sync': False,
        'supports_tracking': False,
        'source': 'default-disabled',
    }


@pytest.mark.asyncio
async def test_status_connection_state_reflects_live_alpaca_connected():
    telescope = Telescope()
    telescope.set_connection_state('disconnected')
    handler = GetTelescopeStatusQueryHandler(
        telescope_repository=FakeRepo(telescope),
        alpaca_client=FakeAlpacaClient(
            AlpacaLiveSnapshot(
                reachable=True,
                connected=True,
                tracking=False,
                supports_slew=True,
                supports_sync=True,
                supports_tracking=True,
                device_name='HW',
            ),
        ),
    )
    payload = await handler.handle(GetTelescopeStatusQuery())
    assert payload['connection_state'] == 'connected'


@pytest.mark.asyncio
async def test_status_connection_state_disconnected_when_alpaca_unreachable():
    telescope = Telescope()
    telescope.set_connection_state('connected')
    handler = GetTelescopeStatusQueryHandler(
        telescope_repository=FakeRepo(telescope),
        alpaca_client=FakeAlpacaClient(
            AlpacaLiveSnapshot(
                reachable=False,
                error_hint='timeout',
            ),
        ),
    )
    payload = await handler.handle(GetTelescopeStatusQuery())
    assert payload['connection_state'] == 'disconnected'


@pytest.mark.asyncio
async def test_status_tracking_enabled_follows_live_alpaca_when_connected():
    telescope = Telescope()
    telescope.set_tracking_enabled(True)
    handler = GetTelescopeStatusQueryHandler(
        telescope_repository=FakeRepo(telescope),
        alpaca_client=FakeAlpacaClient(
            AlpacaLiveSnapshot(
                reachable=True,
                connected=True,
                tracking=False,
                supports_slew=True,
                supports_sync=True,
                supports_tracking=True,
                device_name='HW',
            ),
        ),
    )
    payload = await handler.handle(GetTelescopeStatusQuery())
    assert payload['tracking_enabled'] is False


@pytest.mark.asyncio
async def test_status_tracking_enabled_false_when_scope_not_connected():
    telescope = Telescope()
    telescope.set_tracking_enabled(True)
    handler = GetTelescopeStatusQueryHandler(
        telescope_repository=FakeRepo(telescope),
        alpaca_client=FakeAlpacaClient(
            AlpacaLiveSnapshot(
                reachable=True,
                connected=False,
                tracking=None,
                supports_slew=True,
                supports_sync=True,
                supports_tracking=True,
                device_name='HW',
            ),
        ),
    )
    payload = await handler.handle(GetTelescopeStatusQuery())
    assert payload['tracking_enabled'] is False


@pytest.mark.asyncio
async def test_status_tracking_enabled_keeps_persisted_when_alpaca_unreachable():
    telescope = Telescope()
    telescope.set_tracking_enabled(True)
    handler = GetTelescopeStatusQueryHandler(
        telescope_repository=FakeRepo(telescope),
        alpaca_client=FakeAlpacaClient(
            AlpacaLiveSnapshot(
                reachable=False,
                error_hint='timeout',
            ),
        ),
    )
    payload = await handler.handle(GetTelescopeStatusQuery())
    assert payload['tracking_enabled'] is True
