from dataclasses import dataclass

from domain.ports.alpaca_client import IAlpacaClient
from infra.repositories.telescope.base import BaseTelescopeRepository
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


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
            alpaca_live = {
                'reachable': live.reachable,
                'connected': live.connected,
                'tracking': live.tracking,
                'device_name': live.device_name,
                'error_hint': live.error_hint,
            }

        return {
            'oid': telescope.oid,
            'name': telescope.name,
            'connection_state': telescope.connection_state,
            'tracking_enabled': telescope.tracking_enabled,
            'created_at': telescope.created_at.isoformat(),
            'alpaca_live': alpaca_live,
        }
