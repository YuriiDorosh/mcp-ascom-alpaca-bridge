from dataclasses import dataclass

from domain.ports.alpaca_client import IAlpacaTelescopeClient
from logic.commands.base import (
    BaseCommand,
    CommandHandler,
)


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

    async def handle(self, command: SlewToIcrsCommand) -> dict:
        await self.alpaca_telescope.slew_to_icrs(command.ra_hours, command.dec_degrees)
        return {'status': 'ok'}


@dataclass(frozen=True)
class SyncMountToIcrsCommandHandler(CommandHandler[SyncMountToIcrsCommand, dict]):
    alpaca_telescope: IAlpacaTelescopeClient

    async def handle(self, command: SyncMountToIcrsCommand) -> dict:
        await self.alpaca_telescope.sync_mount_to_icrs(command.ra_hours, command.dec_degrees)
        return {'status': 'ok'}


@dataclass(frozen=True)
class SetTelescopeTrackingCommandHandler(CommandHandler[SetTelescopeTrackingCommand, dict]):
    alpaca_telescope: IAlpacaTelescopeClient

    async def handle(self, command: SetTelescopeTrackingCommand) -> dict:
        await self.alpaca_telescope.set_tracking_enabled(command.enabled)
        return {'status': 'ok'}
