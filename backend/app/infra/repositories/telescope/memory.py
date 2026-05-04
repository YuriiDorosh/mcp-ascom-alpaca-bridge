from dataclasses import dataclass

from domain.entities.telescope import Telescope
from infra.repositories.telescope.base import BaseTelescopeRepository


@dataclass
class InMemoryTelescopeRepository(BaseTelescopeRepository):
    telescope: Telescope

    async def get_primary(self) -> Telescope:
        return self.telescope

    async def save_primary(self, telescope: Telescope) -> Telescope:
        self.telescope = telescope
        return self.telescope
