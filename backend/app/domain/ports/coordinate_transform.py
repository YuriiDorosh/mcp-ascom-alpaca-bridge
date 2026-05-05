from abc import ABC, abstractmethod

from domain.values.coordinates import (
    EquatorialCoordinates,
    HorizontalCoordinates,
)


class ICoordinateTransformService(ABC):
    @abstractmethod
    def equatorial_icrs_to_horizontal(
        self,
        equatorial: EquatorialCoordinates,
        *,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float,
        obstime_utc_iso: str,
    ) -> HorizontalCoordinates:
        """Transform ICRS RA/Dec to local Alt/Az for the given observer and UTC time."""
