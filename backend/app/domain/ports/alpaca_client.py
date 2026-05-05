from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AlpacaLiveSnapshot:
    """Non-authoritative live view from an Alpaca driver (when probing is enabled)."""

    reachable: bool
    connected: bool | None = None
    tracking: bool | None = None
    supports_slew: bool | None = None
    supports_sync: bool | None = None
    supports_tracking: bool | None = None
    device_name: str | None = None
    error_hint: str | None = None


class IAlpacaClient(ABC):
    @abstractmethod
    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        """Return ``None`` when live Alpaca polling is disabled by configuration."""


class IAlpacaTelescopeClient(IAlpacaClient, ABC):
    """Alpaca telescope control (ICRS-equatorial slew/sync plus tracking switches)."""

    @abstractmethod
    async def slew_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        ...

    @abstractmethod
    async def sync_mount_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        ...

    @abstractmethod
    async def set_tracking_enabled(self, enabled: bool) -> None:
        ...
