import asyncio
import time

from domain.ports.alpaca_client import (
    AlpacaLiveSnapshot,
    IAlpacaTelescopeClient,
)
from settings.config import Config


def _blocking_alpaca_snapshot(config: Config) -> AlpacaLiveSnapshot:
    from alpaca.telescope import Telescope

    driver: Telescope | None = None
    try:
        driver = Telescope(
            config.alpaca_address,
            config.alpaca_device_number,
            protocol=config.alpaca_protocol,
        )
        try:
            driver.Connect()
        except AttributeError:
            driver.Connected = True

        deadline = time.monotonic() + config.alpaca_connect_timeout_seconds
        while getattr(driver, 'Connecting', False) and time.monotonic() < deadline:
            time.sleep(0.05)

        if getattr(driver, 'Connecting', False):
            return AlpacaLiveSnapshot(
                reachable=False,
                error_hint='connect-timeout',
            )

        connected = bool(getattr(driver, 'Connected', False))
        tracking = bool(getattr(driver, 'Tracking', False)) if connected else None
        raw_name = getattr(driver, 'Name', None) or getattr(driver, 'Description', None)
        name = None
        if raw_name is not None:
            name = str(raw_name)[:240]

        return AlpacaLiveSnapshot(
            reachable=True,
            connected=connected,
            tracking=tracking,
            device_name=name,
            error_hint=None,
        )
    except Exception as exc:
        return AlpacaLiveSnapshot(
            reachable=False,
            error_hint=type(exc).__name__,
        )
    finally:
        if driver is not None:
            try:
                driver.Connected = False
            except Exception:
                pass


class AlpycaTelescopeClient(IAlpacaTelescopeClient):
    def __init__(self, config: Config):
        self._config = config

    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        if not self._config.alpaca_enabled:
            return None
        return await asyncio.to_thread(_blocking_alpaca_snapshot, self._config)
