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
    assert payload['applied_filters']['include_disabled_commands'] is True
    assert payload['stats']['baseline_steps'] == payload['stats']['returned_steps']
    assert payload['stats']['filtered_out_steps'] == 0
    assert payload['hardware_readiness']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_smoke_plan']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert len(payload['hardware_smoke_plan']['steps']) >= 4
    assert payload['hardware_validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert len(payload['hardware_validation_plan']['steps']) >= 4
    assert payload['hardware_overview']['readiness']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_overview']['validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert len(payload['hardware_overview']['smoke_plan']['steps']) >= 4
    assert len(payload['hardware_overview']['validation_plan']['steps']) >= 4
    steps = {step['tool_name']: step for step in payload['steps']}
    assert 'telescope.get_site_weather' in steps
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
    assert 'telescope.get_site_weather' in steps
    assert payload['hardware_smoke_plan']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert payload['hardware_overview']['smoke_plan']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_overview']['validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert payload['hardware_overview']['smoke_plan']['steps'][0]['step'] == 1
    assert payload['hardware_overview']['validation_plan']['steps'][0]['step'] == 1
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
    assert payload['hardware_smoke_plan']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert payload['hardware_overview']['readiness']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_overview']['smoke_plan']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert len(payload['hardware_overview']['smoke_plan']['steps']) >= 4
    assert len(payload['hardware_overview']['validation_plan']['steps']) >= 4
    assert steps['telescope.get_status']['enabled'] is True
    assert steps['telescope.slew_icrs']['enabled'] is False
    assert steps['telescope.slew_icrs']['skip_reason'] == 'missing_capability:supports_slew'


def test_mcp_execution_plan_can_filter_disabled_command_steps(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='secret-token')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, FakeMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-execution-plan?include_disabled_commands=false')
    assert response.status_code == 200
    payload = response.json()

    tool_names = [step['tool_name'] for step in payload['steps']]
    assert payload['applied_filters']['include_disabled_commands'] is False
    assert payload['stats']['returned_steps'] < payload['stats']['baseline_steps']
    assert payload['stats']['filtered_out_steps'] == payload['stats']['baseline_steps'] - payload['stats']['returned_steps']
    assert 'telescope.slew_icrs' in tool_names
    assert 'telescope.sync_icrs' not in tool_names
    assert 'telescope.set_tracking' not in tool_names
