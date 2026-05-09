from dataclasses import dataclass

import orjson

from domain.ports.alpaca_client import IAlpacaTelescopeClient
from infra.message_brokers.base import BaseMessageBroker
from infra.message_brokers.contracts import TelescopeOperationEventContract
from infra.repositories.operations.base import BaseModelInferenceRepository
from logic.commands.base import (
    BaseCommand,
    CommandHandler,
)
from settings.config import Config


def normalize_ra_hours(value: float) -> float:
    """Wrap RA to ``[0, 24)`` hours."""

    scaled = value % 24.0
    if scaled < 0:
        scaled += 24.0
    return scaled


def clamp_dec_degrees(value: float) -> float:
    return max(-90.0, min(90.0, value))


def apply_equatorial_nudge(
    *,
    ra_hours: float,
    dec_degrees: float,
    delta_ra_sidereal_seconds: float,
    delta_dec_arcseconds: float,
) -> tuple[float, float]:
    """Apply small equatorial offsets (same convention as ASCOM: RA in hours, Dec in degrees).

    East-positive ``delta_ra_sidereal_seconds`` shifts RA by ``delta / 3600`` hours along the equatorial axis
    in sidereal time units. North-positive ``delta_dec_arcseconds`` adds ``delta / 3600`` degrees of declination.
    """

    ra_next = normalize_ra_hours(ra_hours + delta_ra_sidereal_seconds / 3600.0)
    dec_next = clamp_dec_degrees(dec_degrees + delta_dec_arcseconds / 3600.0)
    return ra_next, dec_next


@dataclass(frozen=True)
class SlewToIcrsCommand(BaseCommand):
    ra_hours: float
    dec_degrees: float


@dataclass(frozen=True)
class SyncMountToIcrsCommand(BaseCommand):
    ra_hours: float
    dec_degrees: float


@dataclass(frozen=True)
class SetTelescopeTrackingCommand(BaseCommand):
    enabled: bool


@dataclass(frozen=True)
class NudgeMountEquatorialCommand(BaseCommand):
    delta_ra_sidereal_seconds: float
    delta_dec_arcseconds: float


@dataclass(frozen=True)
class SlewToIcrsCommandHandler(CommandHandler[SlewToIcrsCommand, dict]):
    alpaca_telescope: IAlpacaTelescopeClient
    message_broker: BaseMessageBroker
    audit_repository: BaseModelInferenceRepository
    config: Config

    async def handle(self, command: SlewToIcrsCommand) -> dict:
        await self.alpaca_telescope.slew_to_icrs(command.ra_hours, command.dec_degrees)
        event = TelescopeOperationEventContract.create(
            operation='slew-icrs',
            target_ra_hours=command.ra_hours,
            target_dec_degrees=command.dec_degrees,
        )
        await self.message_broker.send_message(
            key=event.event_id.encode(),
            topic=self.config.telescope_operation_topic,
            value=orjson.dumps(event.__dict__),
        )
        await self.audit_repository.save_command_audit(
            operation='slew-icrs',
            status='ok',
            details={'ra_hours': command.ra_hours, 'dec_degrees': command.dec_degrees},
            source='main-backend',
        )
        return {'status': 'ok'}


@dataclass(frozen=True)
class SyncMountToIcrsCommandHandler(CommandHandler[SyncMountToIcrsCommand, dict]):
    alpaca_telescope: IAlpacaTelescopeClient
    message_broker: BaseMessageBroker
    audit_repository: BaseModelInferenceRepository
    config: Config

    async def handle(self, command: SyncMountToIcrsCommand) -> dict:
        await self.alpaca_telescope.sync_mount_to_icrs(command.ra_hours, command.dec_degrees)
        event = TelescopeOperationEventContract.create(
            operation='sync-icrs',
            target_ra_hours=command.ra_hours,
            target_dec_degrees=command.dec_degrees,
        )
        await self.message_broker.send_message(
            key=event.event_id.encode(),
            topic=self.config.telescope_operation_topic,
            value=orjson.dumps(event.__dict__),
        )
        await self.audit_repository.save_command_audit(
            operation='sync-icrs',
            status='ok',
            details={'ra_hours': command.ra_hours, 'dec_degrees': command.dec_degrees},
            source='main-backend',
        )
        return {'status': 'ok'}


@dataclass(frozen=True)
class SetTelescopeTrackingCommandHandler(CommandHandler[SetTelescopeTrackingCommand, dict]):
    alpaca_telescope: IAlpacaTelescopeClient
    message_broker: BaseMessageBroker
    audit_repository: BaseModelInferenceRepository
    config: Config

    async def handle(self, command: SetTelescopeTrackingCommand) -> dict:
        await self.alpaca_telescope.set_tracking_enabled(command.enabled)
        event = TelescopeOperationEventContract.create(
            operation='set-tracking',
            tracking_enabled=command.enabled,
        )
        await self.message_broker.send_message(
            key=event.event_id.encode(),
            topic=self.config.telescope_operation_topic,
            value=orjson.dumps(event.__dict__),
        )
        await self.audit_repository.save_command_audit(
            operation='set-tracking',
            status='ok',
            details={'enabled': command.enabled},
            source='main-backend',
        )
        return {'status': 'ok'}


@dataclass(frozen=True)
class NudgeMountEquatorialCommandHandler(CommandHandler[NudgeMountEquatorialCommand, dict]):
    alpaca_telescope: IAlpacaTelescopeClient
    message_broker: BaseMessageBroker
    audit_repository: BaseModelInferenceRepository
    config: Config

    async def handle(self, command: NudgeMountEquatorialCommand) -> dict:
        prior_ra, prior_dec = await self.alpaca_telescope.read_mount_icrs_equatorial()
        target_ra, target_dec = apply_equatorial_nudge(
            ra_hours=prior_ra,
            dec_degrees=prior_dec,
            delta_ra_sidereal_seconds=command.delta_ra_sidereal_seconds,
            delta_dec_arcseconds=command.delta_dec_arcseconds,
        )
        await self.alpaca_telescope.slew_to_icrs(target_ra, target_dec)

        event = TelescopeOperationEventContract.create(
            operation='nudge-equatorial',
            target_ra_hours=target_ra,
            target_dec_degrees=target_dec,
        )
        await self.message_broker.send_message(
            key=event.event_id.encode(),
            topic=self.config.telescope_operation_topic,
            value=orjson.dumps(event.__dict__),
        )
        details = {
            'prior_ra_hours': prior_ra,
            'prior_dec_degrees': prior_dec,
            'target_ra_hours': target_ra,
            'target_dec_degrees': target_dec,
            'delta_ra_sidereal_seconds': command.delta_ra_sidereal_seconds,
            'delta_dec_arcseconds': command.delta_dec_arcseconds,
        }
        await self.audit_repository.save_command_audit(
            operation='nudge-equatorial',
            status='ok',
            details=details,
            source='main-backend',
        )
        return {'status': 'ok', **details}
