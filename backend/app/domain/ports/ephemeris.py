from abc import ABC, abstractmethod

from domain.values.coordinates import EquatorialCoordinates


class IEphemerisService(ABC):
    """Solar-system apparent positions; concrete skyfield wiring follows later."""

    @abstractmethod
    def apparent_equatorial(self, body: str, obstime_utc_iso: str) -> EquatorialCoordinates:
        ...
