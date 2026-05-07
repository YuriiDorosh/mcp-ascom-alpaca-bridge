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
                'supports_sync': True,
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


def test_mcp_bootstrap_aggregates_manifest_and_planning_guide(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='secret-token')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, FakeMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-bootstrap')
    assert response.status_code == 200
    payload = response.json()

    manifest_tools = {tool['tool_name']: tool for tool in payload['manifest']['tools']}
    assert manifest_tools['telescope.slew_icrs']['requirements']['requires_command_token'] is True
    assert manifest_tools['model.enqueue_and_wait_inference']['endpoint'] == '/telescopes/model/inference/enqueue-and-wait'
    effective_tools = {tool['tool_name']: tool for tool in payload['effective_manifest']['tools']}
    assert effective_tools['telescope.slew_icrs']['enabled'] is True
    assert effective_tools['telescope.set_tracking']['enabled'] is False

    planning_guide = payload['planning_guide']
    assert planning_guide['objective']
    assert planning_guide['inference_flow'][0]['tool_name'] == 'model.enqueue_inference'
    hardware_readiness = payload['hardware_readiness']
    assert hardware_readiness['requires_real_telescope_now'] is False
    assert hardware_readiness['trigger_task_id'] == 'P5-HW-SMOKE'
    smoke_plan = payload['hardware_smoke_plan']
    assert smoke_plan['trigger_task_id'] == 'P5-HW-SMOKE'
    assert len(smoke_plan['steps']) >= 4
    assert smoke_plan['steps'][0]['step'] == 1
    validation_plan = payload['hardware_validation_plan']
    assert validation_plan['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert len(validation_plan['steps']) >= 4
    assert validation_plan['steps'][0]['step'] == 1
    overview = payload['hardware_overview']
    assert overview['readiness']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert overview['smoke_plan']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert overview['validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert len(overview['smoke_plan']['steps']) >= 4
    assert len(overview['validation_plan']['steps']) >= 4
    assert overview['smoke_plan']['steps'][0]['step'] == 1
    assert overview['validation_plan']['steps'][0]['step'] == 1


def test_mcp_bootstrap_falls_back_to_safe_effective_manifest_when_status_unavailable(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config, FailingMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-bootstrap')
    assert response.status_code == 200
    payload = response.json()

    effective_tools = {tool['tool_name']: tool for tool in payload['effective_manifest']['tools']}
    assert effective_tools['telescope.slew_icrs']['enabled'] is False
    assert effective_tools['telescope.sync_icrs']['enabled'] is False
    assert effective_tools['telescope.set_tracking']['enabled'] is False
    assert effective_tools['telescope.get_status']['enabled'] is True
    assert payload['hardware_readiness']['requires_real_telescope_now'] is False
    assert payload['hardware_smoke_plan']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert payload['hardware_overview']['readiness']['trigger_task_id'] == 'P5-HW-SMOKE'
    assert payload['hardware_overview']['validation_plan']['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert len(payload['hardware_overview']['smoke_plan']['steps']) >= 4
    assert len(payload['hardware_overview']['validation_plan']['steps']) >= 4
