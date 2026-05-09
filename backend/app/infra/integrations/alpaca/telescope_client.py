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
    supports_slew = bool(getattr(driver, 'CanSlew', False))
    supports_sync = bool(getattr(driver, 'CanSync', False))
    supports_tracking = bool(getattr(driver, 'CanSetTracking', connected))
    raw_name = getattr(driver, 'Name', None) or getattr(driver, 'Description', None)
    name = None
    if raw_name is not None:
        name = str(raw_name)[:240]

    return AlpacaLiveSnapshot(
        reachable=True,
        connected=connected,
        tracking=tracking,
        supports_slew=supports_slew,
        supports_sync=supports_sync,
        supports_tracking=supports_tracking,
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


def _wait_until_not_slewing(driver: Any, config: Config) -> None:
    """Poll ``Slewing`` after an async slew; Alpaca devices do not support blocking sync slews."""

    deadline = time.monotonic() + float(config.alpaca_slew_timeout_seconds)
    interval = float(config.alpaca_slew_poll_interval_seconds)

    while time.monotonic() < deadline:
        try:
            if not bool(getattr(driver, 'Slewing', False)):
                return
        except AlpacaRequestException as exc:
            raise AlpacaDriverException(f'Failed to read Slewing while waiting for slew: {exc}') from exc
        time.sleep(interval)

    raise AlpacaDriverException(
        f'Alpaca slew timed out after {config.alpaca_slew_timeout_seconds}s (Slewing did not clear).',
    )


def _blocking_slew(config: Config, ra_hours: float, dec_degrees: float) -> None:
    def work(driver: Any) -> None:
        can_async = bool(getattr(driver, 'CanSlewAsync', False))
        can_sync = bool(getattr(driver, 'CanSlew', False))

        if can_async:
            # ASCOM Alpaca: synchronous slews are invalid over HTTP; Seestar and other Alpaca hosts return 0x400.
            async_method = getattr(driver, 'SlewToCoordinatesAsync', None)
            if async_method is None:
                raise AlpacaDriverException('Mount reports CanSlewAsync=True but SlewToCoordinatesAsync is missing.')
            async_method(float(ra_hours), float(dec_degrees))
            _wait_until_not_slewing(driver, config)
            return

        if can_sync:
            driver.SlewToCoordinates(float(ra_hours), float(dec_degrees))
            return

        raise AlpacaDriverException('Mount reports neither CanSlewAsync nor CanSlew; cannot slew.')

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


def _blocking_read_mount_icrs(config: Config) -> tuple[float, float]:
    """Read Alpaca ``RightAscension`` / ``Declination`` while connected (same units as slew)."""

    def work(driver: Any) -> tuple[float, float]:
        if not bool(getattr(driver, 'Connected', False)):
            raise AlpacaDriverException('Telescope is not connected; cannot read equatorial coordinates.')

        ra_raw = getattr(driver, 'RightAscension', None)
        dec_raw = getattr(driver, 'Declination', None)
        if ra_raw is None or dec_raw is None:
            raise AlpacaDriverException(
                'Alpaca driver does not expose RightAscension/Declination for this device profile.',
            )

        return float(ra_raw), float(dec_raw)

    return _blocking_transaction(config, work)


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

    async def read_mount_icrs_equatorial(self) -> tuple[float, float]:
        self._require_hardware_control()
        return await asyncio.to_thread(_blocking_read_mount_icrs, self._config)

    async def slew_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self._require_hardware_control()
        await asyncio.to_thread(_blocking_slew, self._config, ra_hours, dec_degrees)

    async def sync_mount_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self._require_hardware_control()
        await asyncio.to_thread(_blocking_sync_mount, self._config, ra_hours, dec_degrees)

    async def set_tracking_enabled(self, enabled: bool) -> None:
        self._require_hardware_control()
        await asyncio.to_thread(_blocking_set_tracking, self._config, enabled)
