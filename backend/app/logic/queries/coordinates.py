from dataclasses import dataclass

from domain.exceptions.telescope import CoordinateTransformException
from domain.ports.coordinate_transform import ICoordinateTransformService
from domain.values.coordinates import EquatorialCoordinates
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


@dataclass(frozen=True)
class GetHorizontalFromIcrsQuery(BaseQuery):
    ra_hours: float
    dec_degrees: float
    latitude_deg: float
    longitude_deg: float
    elevation_m: float
    obstime_utc_iso: str


@dataclass(frozen=True)
class GetHorizontalFromIcrsQueryHandler(BaseQueryHandler[GetHorizontalFromIcrsQuery, dict]):
    transforms: ICoordinateTransformService

    async def handle(self, query: GetHorizontalFromIcrsQuery) -> dict:
        eq = EquatorialCoordinates(ra_hours=query.ra_hours, dec_degrees=query.dec_degrees)
        try:
            horizontal = self.transforms.equatorial_icrs_to_horizontal(
                eq,
                latitude_deg=query.latitude_deg,
                longitude_deg=query.longitude_deg,
                elevation_m=query.elevation_m,
                obstime_utc_iso=query.obstime_utc_iso,
            )
        except Exception as exc:
            raise CoordinateTransformException(str(exc)) from exc

        return {
            'altitude_deg': horizontal.altitude_deg,
            'azimuth_deg': horizontal.azimuth_deg,
            'obstime_utc': query.obstime_utc_iso,
        }
