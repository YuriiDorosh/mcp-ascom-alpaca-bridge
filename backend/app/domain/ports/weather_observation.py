from typing import (
    Protocol,
    runtime_checkable,
)


@runtime_checkable
class IWeatherObservationService(Protocol):
    """Portable surface observation snapshot (typically grid-point / METAR-ish, not telescope-local)."""

    async def fetch_current_observation(self, *, latitude: float, longitude: float) -> dict:
        """Return a plain dict aligned with SiteWeatherObservationSchema."""
