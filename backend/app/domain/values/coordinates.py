from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EquatorialCoordinates:
    """Topocentric-independent ICRS-style equatorial coordinates."""

    ra_hours: float
    dec_degrees: float


@dataclass(frozen=True, slots=True)
class HorizontalCoordinates:
    """Local alt/az with azimuth measured east of north (IAU / Astropy AltAz)."""

    altitude_deg: float
    azimuth_deg: float
