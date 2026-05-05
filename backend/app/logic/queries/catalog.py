from dataclasses import dataclass

from domain.exceptions.telescope import UnresolvedObjectNameException
from domain.ports.catalog_resolve import ICatalogResolveService
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


@dataclass(frozen=True)
class ResolveCommonNameToIcrsQuery(BaseQuery):
    """Resolve a celestial object designation to approximate ICRS equatorial."""

    designation: str


@dataclass(frozen=True)
class ResolveCommonNameToIcrsHandler(BaseQueryHandler[ResolveCommonNameToIcrsQuery, dict]):
    catalog: ICatalogResolveService

    async def handle(self, query: ResolveCommonNameToIcrsQuery) -> dict:
        designation = query.designation.strip()
        position = await self.catalog.resolve_common_name(designation)
        if position is None:
            raise UnresolvedObjectNameException(object_name=designation)
        return {
            'designation': designation,
            'ra_hours': position.ra_hours,
            'dec_degrees': position.dec_degrees,
        }
