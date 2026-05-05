import pytest
import orjson

from domain.ports.alpaca_client import (
    AlpacaLiveSnapshot,
    IAlpacaTelescopeClient,
)
from infra.message_brokers.base import BaseMessageBroker
from logic.commands.telescope_control import (
    SetTelescopeTrackingCommand,
    SetTelescopeTrackingCommandHandler,
    SlewToIcrsCommand,
    SlewToIcrsCommandHandler,
    SyncMountToIcrsCommand,
    SyncMountToIcrsCommandHandler,
)
from logic.mediator.base import Mediator


class RecordingTelescopePort(IAlpacaTelescopeClient):
    """Fake Alpaca telescope for dispatch checks (no Alpaca RPC)."""

    def __init__(self) -> None:
        self.slew_calls: list[tuple[float, float]] = []
        self.sync_calls: list[tuple[float, float]] = []
        self.tracking_calls: list[bool] = []

    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        return None

    async def slew_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self.slew_calls.append((ra_hours, dec_degrees))

    async def sync_mount_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        self.sync_calls.append((ra_hours, dec_degrees))

    async def set_tracking_enabled(self, enabled: bool) -> None:
        self.tracking_calls.append(enabled)


class RecordingBroker(BaseMessageBroker):
    def __init__(self) -> None:
        self.messages: list[tuple[bytes, str, bytes]] = []

    async def start(self):
        return None

    async def close(self):
        return None

    async def send_message(self, key: str, topic: str, value: bytes):
        self.messages.append((key, topic, value))

    async def start_consuming(self, topic: str):
        if False:
            yield topic

    async def stop_consuming(self, topic: str):
        return None


class StubConfig:
    telescope_operation_topic = 'telescope-operation-events'


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.records: list[dict] = []

    async def save_command_audit(self, *, operation: str, status: str, details: dict, source: str) -> dict:
        payload = {
            'operation': operation,
            'status': status,
            'details': details,
            'source': source,
        }
        self.records.append(payload)
        return payload


@pytest.mark.asyncio
async def test_command_handlers_invoke_alpaca_port():
    port = RecordingTelescopePort()
    broker = RecordingBroker()
    audit_repo = RecordingAuditRepository()
    config = StubConfig()
    mediator = Mediator()

    slew_h = SlewToIcrsCommandHandler(
        _mediator=mediator,
        alpaca_telescope=port,
        message_broker=broker,
        audit_repository=audit_repo,
        config=config,
    )
    sync_h = SyncMountToIcrsCommandHandler(
        _mediator=mediator,
        alpaca_telescope=port,
        message_broker=broker,
        audit_repository=audit_repo,
        config=config,
    )
    track_h = SetTelescopeTrackingCommandHandler(
        _mediator=mediator,
        alpaca_telescope=port,
        message_broker=broker,
        audit_repository=audit_repo,
        config=config,
    )

    assert await slew_h.handle(SlewToIcrsCommand(ra_hours=5.5, dec_degrees=10.25)) == {'status': 'ok'}
    assert await sync_h.handle(SyncMountToIcrsCommand(ra_hours=5.5, dec_degrees=10.25)) == {'status': 'ok'}
    assert await track_h.handle(SetTelescopeTrackingCommand(enabled=True)) == {'status': 'ok'}

    assert port.slew_calls == [(5.5, 10.25)]
    assert port.sync_calls == [(5.5, 10.25)]
    assert port.tracking_calls == [True]
    assert len(broker.messages) == 3
    topics = [topic for _key, topic, _value in broker.messages]
    assert topics == ['telescope-operation-events', 'telescope-operation-events', 'telescope-operation-events']

    payloads = [orjson.loads(value) for _key, _topic, value in broker.messages]
    assert payloads[0]['operation'] == 'slew-icrs'
    assert payloads[1]['operation'] == 'sync-icrs'
    assert payloads[2]['operation'] == 'set-tracking'
    assert payloads[0]['schema_version'] == 'v1'
    assert payloads[1]['schema_version'] == 'v1'
    assert payloads[2]['schema_version'] == 'v1'
    assert payloads[0]['correlation_id'] == payloads[0]['event_id']
    assert [record['operation'] for record in audit_repo.records] == ['slew-icrs', 'sync-icrs', 'set-tracking']
