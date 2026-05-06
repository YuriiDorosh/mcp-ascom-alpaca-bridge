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


def test_mcp_tool_manifest_exposes_capability_and_auth_requirements(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='secret-token')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-manifest')
    assert response.status_code == 200
    payload = response.json()

    tools = {tool['tool_name']: tool for tool in payload['tools']}
    assert tools['telescope.slew_icrs']['requirements'] == {
        'required_capability': 'supports_slew',
        'requires_command_token': True,
    }
    assert tools['telescope.sync_icrs']['requirements'] == {
        'required_capability': 'supports_sync',
        'requires_command_token': True,
    }
    assert tools['telescope.set_tracking']['requirements'] == {
        'required_capability': 'supports_tracking',
        'requires_command_token': True,
    }
    assert tools['telescope.get_context']['requirements'] == {
        'required_capability': None,
        'requires_command_token': False,
    }


def test_mcp_tool_manifest_marks_command_token_optional_when_not_configured(monkeypatch):
    config = Config(COMMAND_AUTH_TOKEN='')
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(config))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-manifest')
    assert response.status_code == 200
    payload = response.json()
    tools = {tool['tool_name']: tool for tool in payload['tools']}
    assert tools['telescope.slew_icrs']['requirements']['requires_command_token'] is False
