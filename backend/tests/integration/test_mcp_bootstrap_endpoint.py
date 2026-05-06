from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from settings.config import Config


class FakeContainer:
    def __init__(self, config: Config):
        self._config = config

    def resolve(self, cls):
        if cls is Config:
            return self._config
        raise KeyError(cls)


def test_mcp_bootstrap_aggregates_manifest_and_planning_guide(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='secret-token')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-bootstrap')
    assert response.status_code == 200
    payload = response.json()

    manifest_tools = {tool['tool_name']: tool for tool in payload['manifest']['tools']}
    assert manifest_tools['telescope.slew_icrs']['requirements']['requires_command_token'] is True
    assert manifest_tools['model.enqueue_and_wait_inference']['endpoint'] == '/telescopes/model/inference/enqueue-and-wait'

    planning_guide = payload['planning_guide']
    assert planning_guide['objective']
    assert planning_guide['inference_flow'][0]['tool_name'] == 'model.enqueue_inference'
