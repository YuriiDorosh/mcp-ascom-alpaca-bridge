"""Deterministic assertions for RA/Dec -> Alt/Az using a fixed UTC instant."""

import pytest

from domain.values.coordinates import EquatorialCoordinates
from infra.integrations.astropy.coordinate_transform import AstropyCoordinateTransformService


def test_icrs_to_horizontal_matches_astropy_snapshot():
    service = AstropyCoordinateTransformService()
    horizontal = service.equatorial_icrs_to_horizontal(
        EquatorialCoordinates(ra_hours=12.0, dec_degrees=45.0),
        latitude_deg=52.0,
        longitude_deg=21.0,
        elevation_m=120.0,
        obstime_utc_iso='2026-05-05T12:00:00',
    )

    assert horizontal.altitude_deg == pytest.approx(21.387132, abs=5e-6)
    assert horizontal.azimuth_deg == pytest.approx(43.192250, abs=5e-6)
