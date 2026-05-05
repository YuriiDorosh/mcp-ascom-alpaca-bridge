import orjson
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router


class RecordingTelescopePort(IAlpacaTelescopeClient):
    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        return None

    async def slew_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        return None

    async def sync_mount_to_icrs(self, ra_hours: float, dec_degrees: float) -> None:
        return None

    async def set_tracking_enabled(self, enabled: bool) -> None:
        return None


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
    command_auth_token = None


class FakeContainer:
    def __init__(self, mediator: Mediator, config: StubConfig):
        self._mediator = mediator
        self._config = config

    def resolve(self, cls):
        from settings.config import Config

        if cls is Mediator:
            return self._mediator
        if cls is Config:
            return self._config
        raise KeyError(cls)


def _build_test_app(broker: RecordingBroker, monkeypatch, *, command_auth_token: str | None = None) -> FastAPI:
    mediator = Mediator()
    alpaca = RecordingTelescopePort()
    config = StubConfig()
    config.command_auth_token = command_auth_token

    mediator.register_command(
        SlewToIcrsCommand,
        [SlewToIcrsCommandHandler(_mediator=mediator, alpaca_telescope=alpaca, message_broker=broker, config=config)],
    )
    mediator.register_command(
        SyncMountToIcrsCommand,
        [SyncMountToIcrsCommandHandler(_mediator=mediator, alpaca_telescope=alpaca, message_broker=broker, config=config)],
    )
    mediator.register_command(
        SetTelescopeTrackingCommand,
        [SetTelescopeTrackingCommandHandler(_mediator=mediator, alpaca_telescope=alpaca, message_broker=broker, config=config)],
    )

    fake_container = FakeContainer(mediator=mediator, config=config)
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: fake_container)

    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    return app


def test_telescope_commands_publish_operation_events(monkeypatch):
    broker = RecordingBroker()
    app = _build_test_app(broker, monkeypatch)
    client = TestClient(app)

    r1 = client.post('/telescopes/commands/slew-icrs', json={'ra_hours': 5.1, 'dec_degrees': -12.4})
    r2 = client.post('/telescopes/commands/sync-icrs', json={'ra_hours': 5.1, 'dec_degrees': -12.4})
    r3 = client.post('/telescopes/commands/tracking', json={'enabled': True})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200
    assert len(broker.messages) == 3
    assert [t for _k, t, _v in broker.messages] == ['telescope-operation-events'] * 3

    payloads = [orjson.loads(v) for _k, _t, v in broker.messages]
    assert payloads[0]['operation'] == 'slew-icrs'
    assert payloads[1]['operation'] == 'sync-icrs'
    assert payloads[2]['operation'] == 'set-tracking'
    assert all(payload['schema_version'] == 'v1' for payload in payloads)
    assert all(payload['correlation_id'] == payload['event_id'] for payload in payloads)


def test_telescope_command_auth_guard_requires_token_when_configured(monkeypatch):
    broker = RecordingBroker()
    app = _build_test_app(broker, monkeypatch, command_auth_token='secret-token')
    client = TestClient(app)

    unauthorized = client.post('/telescopes/commands/tracking', json={'enabled': True})
    authorized = client.post(
        '/telescopes/commands/tracking',
        json={'enabled': True},
        headers={'X-Command-Token': 'secret-token'},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
