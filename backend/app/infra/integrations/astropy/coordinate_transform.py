from astropy import units as u
from astropy.coordinates import (
    AltAz,
    EarthLocation,
    SkyCoord,
)
from astropy.time import Time

from domain.ports.coordinate_transform import ICoordinateTransformService
from domain.values.coordinates import (
    EquatorialCoordinates,
    HorizontalCoordinates,
)


class AstropyCoordinateTransformService(ICoordinateTransformService):
    def equatorial_icrs_to_horizontal(
        self,
        equatorial: EquatorialCoordinates,
        *,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float,
        obstime_utc_iso: str,
    ) -> HorizontalCoordinates:
        location = EarthLocation(
            lat=latitude_deg * u.deg,
            lon=longitude_deg * u.deg,
            height=elevation_m * u.m,
        )
        obstime = Time(obstime_utc_iso, scale='utc')
        sky = SkyCoord(
            ra=equatorial.ra_hours * u.hourangle,
            dec=equatorial.dec_degrees * u.deg,
            frame='icrs',
        )
        frame = AltAz(obstime=obstime, location=location)
        alt_az = sky.transform_to(frame)

        return HorizontalCoordinates(
            altitude_deg=float(alt_az.alt.deg),
            azimuth_deg=float(alt_az.az.deg),
        )
