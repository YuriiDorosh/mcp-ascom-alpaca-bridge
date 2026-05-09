from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from domain.entities.telescope import Telescope
from domain.ports.alpaca_client import (
    AlpacaLiveSnapshot,
    IAlpacaClient,
)
from infra.repositories.telescope.base import BaseTelescopeRepository
from logic.mediator.base import Mediator
from logic.queries.telescope import (
    GetTelescopeStatusQuery,
    GetTelescopeStatusQueryHandler,
)


class _FakeTelescopeRepo(BaseTelescopeRepository):
    def __init__(self, telescope: Telescope):
        self._telescope = telescope

    async def get_primary(self) -> Telescope:
        return self._telescope

    async def save_primary(self, telescope: Telescope) -> Telescope:
        return telescope


class _FakeAlpaca(IAlpacaClient):
    def __init__(self, snapshot: AlpacaLiveSnapshot | None):
        self._snapshot = snapshot

    async def read_live_telescope_snapshot(self) -> AlpacaLiveSnapshot | None:
        return self._snapshot


class _MiniContainer:
    def __init__(self, mediator: Mediator):
        self._mediator = mediator

    def resolve(self, cls):
        if cls is Mediator:
            return self._mediator
        raise KeyError(cls)


def _status_mediator(repo: BaseTelescopeRepository, alpaca: IAlpacaClient) -> Mediator:
    mediator = Mediator()
    mediator.register_query(
        GetTelescopeStatusQuery,
        GetTelescopeStatusQueryHandler(
            telescope_repository=repo,
            alpaca_client=alpaca,
        ),
    )
    return mediator


def _client_for_telescope(monkeypatch, telescope: Telescope, snapshot: AlpacaLiveSnapshot | None) -> TestClient:
    mediator = _status_mediator(_FakeTelescopeRepo(telescope), _FakeAlpaca(snapshot))
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: _MiniContainer(mediator))

    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    return TestClient(app)


def test_telescope_status_endpoint_serializes_live_overlay(monkeypatch):
    telescope = Telescope()
    telescope.set_connection_state('disconnected')
    telescope.set_tracking_enabled(True)
    client = _client_for_telescope(
        monkeypatch,
        telescope,
        AlpacaLiveSnapshot(
            reachable=True,
            connected=True,
            tracking=False,
            supports_slew=True,
            supports_sync=True,
            supports_tracking=True,
            device_name='Integration',
        ),
    )

    response = client.get('/telescopes/status')
    assert response.status_code == 200
    payload = response.json()

    assert payload['connection_state'] == 'connected'
    assert payload['tracking_enabled'] is False
    assert payload['alpaca_live'] is not None
    assert payload['alpaca_live']['connected'] is True
    assert payload['capabilities']['source'] == 'alpaca-live'


def test_telescope_status_without_live_probe_returns_persisted_fields(monkeypatch):
    telescope = Telescope()
    telescope.set_connection_state('connected')
    telescope.set_tracking_enabled(True)
    client = _client_for_telescope(monkeypatch, telescope, None)

    payload = client.get('/telescopes/status').json()

    assert payload['connection_state'] == 'connected'
    assert payload['tracking_enabled'] is True
    assert payload['alpaca_live'] is None
    assert payload['capabilities']['source'] == 'default-disabled'


def test_telescope_status_unreachable_alpaca_clears_connection_overlay(monkeypatch):
    telescope = Telescope()
    telescope.set_connection_state('connected')
    telescope.set_tracking_enabled(True)
    client = _client_for_telescope(
        monkeypatch,
        telescope,
        AlpacaLiveSnapshot(reachable=False, error_hint='timeout'),
    )

    payload = client.get('/telescopes/status').json()

    assert payload['connection_state'] == 'disconnected'
    assert payload['tracking_enabled'] is True
    assert payload['alpaca_live']['reachable'] is False


def test_telescope_status_reachable_but_not_connected_forces_disconnected_and_no_tracking(monkeypatch):
    telescope = Telescope()
    telescope.set_connection_state('connected')
    telescope.set_tracking_enabled(True)
    client = _client_for_telescope(
        monkeypatch,
        telescope,
        AlpacaLiveSnapshot(
            reachable=True,
            connected=False,
            tracking=None,
            supports_slew=True,
            supports_sync=True,
            supports_tracking=True,
            device_name='Integration',
        ),
    )

    payload = client.get('/telescopes/status').json()

    assert payload['connection_state'] == 'disconnected'
    assert payload['tracking_enabled'] is False
    assert payload['alpaca_live']['connected'] is False
