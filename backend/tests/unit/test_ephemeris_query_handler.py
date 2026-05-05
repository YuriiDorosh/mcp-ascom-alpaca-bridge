import pytest

from domain.ports.ephemeris import IEphemerisService
from domain.values.coordinates import EquatorialCoordinates
from logic.queries.ephemeris import (
    GetSolarSystemBodyIcrsQuery,
    GetSolarSystemBodyIcrsQueryHandler,
)


class FakeEphemerisService(IEphemerisService):
    def apparent_equatorial(self, body: str, obstime_utc_iso: str) -> EquatorialCoordinates:
        assert body == 'mars'
        assert obstime_utc_iso == '2026-05-05T12:00:00+00:00'
        return EquatorialCoordinates(
            ra_hours=12.345,
            dec_degrees=-7.89,
        )


@pytest.mark.asyncio
async def test_get_solar_system_body_icrs_query_handler():
    handler = GetSolarSystemBodyIcrsQueryHandler(ephemeris=FakeEphemerisService())
    result = await handler.handle(
        GetSolarSystemBodyIcrsQuery(
            body='mars',
            obstime_utc_iso='2026-05-05T12:00:00+00:00',
        ),
    )

    assert result == {
        'body': 'mars',
        'obstime_utc': '2026-05-05T12:00:00+00:00',
        'ra_hours': 12.345,
        'dec_degrees': -7.89,
    }
