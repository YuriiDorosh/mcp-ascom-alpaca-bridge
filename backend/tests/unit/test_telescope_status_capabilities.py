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
    async def get_primary(self) -> Telescope:
        return Telescope()

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
