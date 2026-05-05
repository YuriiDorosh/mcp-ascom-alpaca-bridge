import asyncio

from astropy.coordinates import SkyCoord

from domain.exceptions.telescope import (
    CatalogLookupDisabledException,
    CatalogLookupTimeoutException,
)
from domain.ports.catalog_resolve import ICatalogResolveService
from domain.values.coordinates import EquatorialCoordinates
from settings.config import Config


class SesameBackedCatalogResolveService(ICatalogResolveService):
    """Resolves names through Astropy (Sesame / CDS mirror); performs blocking I/O in ``to_thread``."""

    def __init__(self, config: Config):
        self._config = config

    async def resolve_common_name(self, name: str) -> EquatorialCoordinates | None:
        if not self._config.catalog_lookup_enabled:
            raise CatalogLookupDisabledException()

        trimmed = name.strip()
        if not trimmed:
            return None

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._blocking_resolve_icrs, trimmed),
                timeout=self._config.catalog_resolve_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise CatalogLookupTimeoutException() from exc

    def _blocking_resolve_icrs(self, name: str) -> EquatorialCoordinates | None:
        try:
            coord = SkyCoord.from_name(name)
            icrs = coord.icrs
            return EquatorialCoordinates(
                ra_hours=float(icrs.ra.hour),
                dec_degrees=float(icrs.dec.deg),
            )
        except Exception:
            return None
