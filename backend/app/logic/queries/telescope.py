from dataclasses import dataclass

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

    async def handle(self, query: GetTelescopeStatusQuery) -> dict:
        telescope = await self.telescope_repository.get_primary()

        return {
            'oid': telescope.oid,
            'name': telescope.name,
            'connection_state': telescope.connection_state,
            'tracking_enabled': telescope.tracking_enabled,
            'created_at': telescope.created_at.isoformat(),
        }
