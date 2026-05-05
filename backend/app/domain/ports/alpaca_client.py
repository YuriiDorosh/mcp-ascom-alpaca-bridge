from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AlpacaLiveSnapshot:
    """Non-authoritative live view from an Alpaca driver (when probing is enabled)."""

    reachable: bool
    connected: bool | None = None
    tracking: bool | None = None
    device_name: str | None = None
    error_hint: str | None = None


class IAlpacaClient(ABC):
    @abstractmethod
    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        """Return ``None`` when live Alpaca polling is disabled by configuration."""


class IAlpacaTelescopeClient(IAlpacaClient, ABC):
    """Telescope-focused Alpaca port; extend later for slew/sync/tracking commands."""
