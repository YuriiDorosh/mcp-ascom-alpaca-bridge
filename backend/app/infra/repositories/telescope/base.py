from abc import (
    ABC,
    abstractmethod,
)

from domain.entities.telescope import Telescope


class BaseTelescopeRepository(ABC):
    @abstractmethod
    async def get_primary(self) -> Telescope:
        ...

    @abstractmethod
    async def save_primary(self, telescope: Telescope) -> Telescope:
        ...
