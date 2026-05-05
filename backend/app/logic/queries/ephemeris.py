from dataclasses import dataclass

from domain.ports.ephemeris import IEphemerisService
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


@dataclass(frozen=True)
class GetSolarSystemBodyIcrsQuery(BaseQuery):
    body: str
    obstime_utc_iso: str


@dataclass(frozen=True)
class GetSolarSystemBodyIcrsQueryHandler(BaseQueryHandler[GetSolarSystemBodyIcrsQuery, dict]):
    ephemeris: IEphemerisService

    async def handle(self, query: GetSolarSystemBodyIcrsQuery) -> dict:
        position = self.ephemeris.apparent_equatorial(
            body=query.body,
            obstime_utc_iso=query.obstime_utc_iso,
        )
        return {
            'body': query.body.strip().lower(),
            'obstime_utc': query.obstime_utc_iso,
            'ra_hours': position.ra_hours,
            'dec_degrees': position.dec_degrees,
        }
