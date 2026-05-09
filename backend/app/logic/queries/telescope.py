from dataclasses import dataclass

from domain.entities.telescope import Telescope
from domain.ports.alpaca_client import (
    AlpacaLiveSnapshot,
    IAlpacaClient,
)
from infra.repositories.telescope.base import BaseTelescopeRepository
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


def _status_connection_state(persisted: Telescope, live: AlpacaLiveSnapshot | None) -> str:
    """Merge Mongo-backed session state with a live Alpaca snapshot for API responses."""

    stored = persisted.connection_state
    if live is None:
        return stored
    if live.reachable and live.connected is True:
        return 'connected'
    if not live.reachable:
        return 'disconnected'
    if live.connected is False:
        return 'disconnected'
    return stored


@dataclass(frozen=True)
class GetTelescopeStatusQuery(BaseQuery):
    ...


@dataclass(frozen=True)
class GetTelescopeStatusQueryHandler(BaseQueryHandler[GetTelescopeStatusQuery, dict]):
    telescope_repository: BaseTelescopeRepository
    alpaca_client: IAlpacaClient

    async def handle(self, query: GetTelescopeStatusQuery) -> dict:
        telescope = await self.telescope_repository.get_primary()
        live = await self.alpaca_client.read_live_telescope_snapshot()

        alpaca_live = None
        if live is not None:
            capabilities = {
                'supports_slew': bool(live.supports_slew),
                'supports_sync': bool(live.supports_sync),
                'supports_tracking': bool(live.supports_tracking),
                'source': 'alpaca-live',
            }
            alpaca_live = {
                'reachable': live.reachable,
                'connected': live.connected,
                'tracking': live.tracking,
                'supports_slew': live.supports_slew,
                'supports_sync': live.supports_sync,
                'supports_tracking': live.supports_tracking,
                'device_name': live.device_name,
                'error_hint': live.error_hint,
            }
        else:
            capabilities = {
                'supports_slew': False,
                'supports_sync': False,
                'supports_tracking': False,
                'source': 'default-disabled',
            }

        return {
            'oid': telescope.oid,
            'name': telescope.name,
            'connection_state': _status_connection_state(telescope, live),
            'tracking_enabled': telescope.tracking_enabled,
            'created_at': telescope.created_at.isoformat(),
            'alpaca_live': alpaca_live,
            'capabilities': capabilities,
        }
