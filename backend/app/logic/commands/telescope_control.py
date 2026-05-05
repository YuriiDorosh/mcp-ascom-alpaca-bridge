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
