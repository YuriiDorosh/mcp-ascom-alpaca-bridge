from abc import ABC, abstractmethod

from domain.values.coordinates import EquatorialCoordinates


class ICatalogResolveService(ABC):
    @abstractmethod
    async def resolve_common_name(self, name: str) -> EquatorialCoordinates | None:
        ...
