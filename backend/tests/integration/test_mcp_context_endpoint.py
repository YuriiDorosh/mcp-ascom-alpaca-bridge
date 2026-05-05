from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from logic.mediator.base import Mediator
from logic.queries.catalog import ResolveCommonNameToIcrsQuery
from logic.queries.ephemeris import GetSolarSystemBodyIcrsQuery
from logic.queries.telescope import GetTelescopeStatusQuery


class FakeMediator:
    async def handle_query(self, query):
        if isinstance(query, GetTelescopeStatusQuery):
            return {
                'oid': 't1',
                'name': 'Primary Telescope',
                'connection_state': 'disconnected',
                'tracking_enabled': False,
                'created_at': '2026-05-05T12:00:00',
                'alpaca_live': None,
                'capabilities': {
                    'supports_slew': False,
                    'supports_sync': False,
                    'supports_tracking': False,
                    'source': 'default-disabled',
                },
            }
        if isinstance(query, ResolveCommonNameToIcrsQuery):
            return {
                'designation': query.designation,
                'ra_hours': 0.71,
                'dec_degrees': 41.26,
            }
        if isinstance(query, GetSolarSystemBodyIcrsQuery):
            return {
                'body': query.body,
                'obstime_utc': query.obstime_utc_iso,
                'ra_hours': 12.1,
                'dec_degrees': -4.2,
            }
        raise KeyError(type(query).__name__)


class FakeContainer:
    def __init__(self, mediator):
        self._mediator = mediator

    def resolve(self, cls):
        if cls is Mediator:
            return self._mediator
        raise KeyError(cls)


def test_mcp_context_aggregates_status_catalog_and_ephemeris(monkeypatch):
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(FakeMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get(
        '/telescopes/context/mcp',
        params={
            'designation': 'M31',
            'ephemeris_body': 'mars',
            'obstime_utc_iso': '2026-05-05T12:00:00',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['capabilities']['supports_slew'] is False
    assert payload['catalog_target']['designation'] == 'M31'
    assert payload['ephemeris_target']['body'] == 'mars'
    assert payload['warnings'] == []


def test_mcp_context_warns_when_ephemeris_time_missing(monkeypatch):
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(FakeMediator()))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get(
        '/telescopes/context/mcp',
        params={
            'ephemeris_body': 'mars',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['ephemeris_target'] is None
    assert payload['warnings'][0]['code'] == 'missing_obstime'
