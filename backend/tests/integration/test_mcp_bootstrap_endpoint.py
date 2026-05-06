from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
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
