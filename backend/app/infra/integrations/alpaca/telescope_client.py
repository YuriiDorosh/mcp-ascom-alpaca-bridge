import asyncio
import contextlib
import time
from collections.abc import Callable
from typing import Any, TypeVar

from alpaca.exceptions import AlpacaRequestException

from domain.exceptions.telescope import AlpacaDriverException
from domain.ports.alpaca_client import (
    AlpacaLiveSnapshot,
    IAlpacaTelescopeClient,
)
from settings.config import Config

T = TypeVar('T')


def _blocking_transaction(config: Config, work: Callable[[Any], T]) -> T:
    """Connect, run ``work(driver)``, then disconnect. Raises ``AlpacaDriverException``."""

    from alpaca.telescope import Telescope

    driver: Any | None = None
    try:
        driver = Telescope(
            config.alpaca_address,
            config.alpaca_device_number,
            protocol=config.alpaca_protocol,
        )
        _wait_for_connection(driver, config.alpaca_connect_timeout_seconds)

        if not getattr(driver, 'Connected', False):
            raise AlpacaDriverException('Alpaca telescope did not reach Connected=True.')

        return work(driver)

    except AlpacaDriverException:
        raise
    except AlpacaRequestException as exc:
        raise AlpacaDriverException(str(exc)) from exc
    except Exception as exc:
        raise AlpacaDriverException(str(exc)) from exc
    finally:
        if driver is not None:
            with contextlib.suppress(Exception):
                driver.Connected = False


def _wait_for_connection(driver: Any, timeout_seconds: float) -> None:
    try:
        driver.Connect()
    except AttributeError:
        driver.Connected = True

    deadline = time.monotonic() + timeout_seconds
    while getattr(driver, 'Connecting', False) and time.monotonic() < deadline:
        time.sleep(0.05)

    if getattr(driver, 'Connecting', False):
        raise AlpacaDriverException('Alpaca Connect timed out')


def _snapshot_from_driver(driver: Any) -> AlpacaLiveSnapshot:
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


def _blocking_alpaca_snapshot(config: Config) -> AlpacaLiveSnapshot:
    try:
        return _blocking_transaction(config, _snapshot_from_driver)
    except AlpacaDriverException as exc:
        return AlpacaLiveSnapshot(
            reachable=False,
            error_hint=exc.reason[:200],
        )


def _blocking_slew(config: Config, ra_hours: float, dec_degrees: float) -> None:
    def work(driver: Any) -> None:
        if not bool(driver.CanSlew):
            raise AlpacaDriverException('Mount reports CanSlew=False.')
        driver.SlewToCoordinates(float(ra_hours), float(dec_degrees))

    _blocking_transaction(config, work)


def _blocking_sync_mount(config: Config, ra_hours: float, dec_degrees: float) -> None:
    def work(driver: Any) -> None:
        if not bool(driver.CanSync):
            raise AlpacaDriverException('Mount reports CanSync=False.')
        driver.SyncToCoordinates(float(ra_hours), float(dec_degrees))

    _blocking_transaction(config, work)


def _blocking_set_tracking(config: Config, enabled: bool) -> None:
    def work(driver: Any) -> None:
        driver.Tracking = bool(enabled)

    _blocking_transaction(config, work)


class AlpycaTelescopeClient(IAlpacaTelescopeClient):
    def __init__(self, config: Config):
        self._config = config

    def _require_hardware_control(self) -> None:
        if not self._config.alpaca_enabled:
            raise AlpacaDriverException(
                'Alpaca hardware control is disabled; set ALPACA_ENABLED=true in the environment.',
            )

    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        if not self._config.alpaca_enabled:
            return None
        return await asyncio.to_thread(_blocking_alpaca_snapshot, self._config)

    async def slew_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self._require_hardware_control()
        await asyncio.to_thread(_blocking_slew, self._config, ra_hours, dec_degrees)

    async def sync_mount_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self._require_hardware_control()
        await asyncio.to_thread(_blocking_sync_mount, self._config, ra_hours, dec_degrees)

    async def set_tracking_enabled(self, enabled: bool) -> None:
        self._require_hardware_control()
        await asyncio.to_thread(_blocking_set_tracking, self._config, enabled)
