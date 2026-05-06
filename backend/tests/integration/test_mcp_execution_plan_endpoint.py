from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from domain.exceptions.infrastructure import InfrastructureUnavailableException
from logic.mediator.base import Mediator
from settings.config import Config


class FakeMediator(Mediator):
    async def handle_query(self, query):
        return {
            'capabilities': {
                'supports_slew': True,
                'supports_sync': False,
                'supports_tracking': False,
                'source': 'alpaca-live',
            },
        }

    async def handle_command(self, command):
        raise NotImplementedError


class FailingMediator(Mediator):
    async def handle_query(self, query):
        raise InfrastructureUnavailableException('status unavailable')

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


def test_mcp_execution_plan_marks_capability_gated_steps(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='secret-token')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, FakeMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-execution-plan')
    assert response.status_code == 200
    payload = response.json()

    assert payload['mode'] == 'async'
    assert payload['hardware_readiness']['trigger_task_id'] == 'P5-HW-SMOKE'
    steps = {step['tool_name']: step for step in payload['steps']}
    assert 'model.enqueue_inference' in steps
    assert 'model.enqueue_and_wait_inference' not in steps
    assert steps['telescope.slew_icrs']['enabled'] is True
    assert steps['telescope.sync_icrs']['enabled'] is False
    assert steps['telescope.sync_icrs']['skip_reason'] == 'missing_capability:supports_sync'
    assert steps['telescope.set_tracking']['enabled'] is False


def test_mcp_execution_plan_supports_sync_mode(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='secret-token')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, FakeMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-execution-plan?mode=sync')
    assert response.status_code == 200
    payload = response.json()
    assert payload['mode'] == 'sync'
    steps = {step['tool_name']: step for step in payload['steps']}
    assert 'model.enqueue_and_wait_inference' in steps
    assert 'model.enqueue_inference' not in steps
    assert 'model.get_inference_status' not in steps
    assert 'model.wait_inference_result' not in steps


def test_mcp_execution_plan_falls_back_to_safe_disabled_command_steps(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, FailingMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-execution-plan')
    assert response.status_code == 200
    payload = response.json()

    steps = {step['tool_name']: step for step in payload['steps']}
    assert steps['telescope.get_status']['enabled'] is True
    assert steps['telescope.slew_icrs']['enabled'] is False
    assert steps['telescope.slew_icrs']['skip_reason'] == 'missing_capability:supports_slew'
