from datetime import datetime

from skyfield.api import load

from domain.exceptions.telescope import (
    EphemerisDisabledException,
    EphemerisUnavailableException,
)
from domain.ports.ephemeris import IEphemerisService
from domain.values.coordinates import EquatorialCoordinates
from settings.config import Config

_SUPPORTED_BODIES = {
    'sun': 'sun',
    'moon': 'moon',
    'mercury': 'mercury',
    'venus': 'venus',
    'mars': 'mars',
    'jupiter': 'jupiter barycenter',
    'saturn': 'saturn barycenter',
    'uranus': 'uranus barycenter',
    'neptune': 'neptune barycenter',
    'pluto': 'pluto barycenter',
}


class SkyfieldEphemerisService(IEphemerisService):
    def __init__(self, config: Config):
        self._config = config

    def apparent_equatorial(self, body: str, obstime_utc_iso: str) -> EquatorialCoordinates:
        if not self._config.ephemeris_enabled:
            raise EphemerisDisabledException()

        body_key = body.strip().lower()
        target_name = _SUPPORTED_BODIES.get(body_key)
        if target_name is None:
            supported = ', '.join(sorted(_SUPPORTED_BODIES.keys()))
            raise EphemerisUnavailableException(f'Unsupported body "{body}". Supported: {supported}')

        try:
            dt = datetime.fromisoformat(obstime_utc_iso.replace('Z', '+00:00'))
            ts = load.timescale()
            eph = load(self._config.ephemeris_kernel)
            earth = eph['earth']
            target = eph[target_name]
            apparent = earth.at(ts.from_datetime(dt)).observe(target).apparent()
            ra, dec, _ = apparent.radec()
        except Exception as exc:
            raise EphemerisUnavailableException(str(exc)) from exc

        return EquatorialCoordinates(
            ra_hours=float(ra.hours),
            dec_degrees=float(dec.degrees),
        )
