from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from domain.exceptions.infrastructure import InfrastructureUnavailableException
from logic.mediator.base import Mediator
from settings.config import Config


class FakeMediator(Mediator):
    def __init__(self, status_payload=None, fail=False):
        self._status_payload = status_payload
        self._fail = fail

    async def handle_query(self, query):
        if self._fail:
            raise InfrastructureUnavailableException('status unavailable')
        return self._status_payload

    async def handle_command(self, command):
        raise NotImplementedError


class FakeContainer:
    def __init__(self, config: Config, mediator: Mediator):
        self._config = config
        self._mediator = mediator

    def resolve(self, cls):
        if cls is Config:
            return self._config
        if cls is Mediator:
            return self._mediator
        raise KeyError(cls)


def test_effective_mcp_manifest_marks_capability_gated_tools_disabled(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='secret-token')
    mediator = FakeMediator(
        status_payload={
            'capabilities': {
                'supports_slew': False,
                'supports_sync': True,
                'supports_tracking': False,
                'source': 'alpaca-live',
            },
        },
    )
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, mediator))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-manifest/effective')
    assert response.status_code == 200
    tools = {item['tool_name']: item for item in response.json()['tools']}

    assert tools['telescope.slew_icrs']['enabled'] is False
    assert tools['telescope.slew_icrs']['disabled_reason'] == 'missing_capability:supports_slew'
    assert tools['telescope.sync_icrs']['enabled'] is True
    assert tools['telescope.sync_icrs']['disabled_reason'] is None
    assert tools['telescope.set_tracking']['enabled'] is False
    assert tools['telescope.set_tracking']['disabled_reason'] == 'missing_capability:supports_tracking'
    assert tools['model.enqueue_inference']['enabled'] is True
    assert tools['model.enqueue_inference']['disabled_reason'] is None


def test_effective_mcp_manifest_falls_back_to_disabled_capabilities_on_status_error(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='')
    mediator = FakeMediator(fail=True)
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, mediator))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-manifest/effective')
    assert response.status_code == 200
    tools = {item['tool_name']: item for item in response.json()['tools']}

    assert tools['telescope.slew_icrs']['enabled'] is False
    assert tools['telescope.sync_icrs']['enabled'] is False
    assert tools['telescope.set_tracking']['enabled'] is False
    assert tools['telescope.slew_icrs']['disabled_reason'] == 'missing_capability:supports_slew'
    assert tools['telescope.sync_icrs']['disabled_reason'] == 'missing_capability:supports_sync'
    assert tools['telescope.set_tracking']['disabled_reason'] == 'missing_capability:supports_tracking'
    assert tools['telescope.get_status']['enabled'] is True
    assert tools['telescope.get_status']['disabled_reason'] is None
