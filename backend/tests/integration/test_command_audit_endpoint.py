from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from logic.mediator.base import Mediator
from logic.queries.command_audit import ListCommandAuditQuery


class FakeMediator:
    async def handle_query(self, query):
        if isinstance(query, ListCommandAuditQuery):
            assert query.operation == 'set-tracking'
            assert query.status == 'ok'
            assert query.source == 'main-backend'
            return [
                {
                    'audit_id': 'a1',
                    'operation': 'set-tracking',
                    'status': 'ok',
                    'details': {'enabled': True},
                    'source': 'main-backend',
                    'recorded_at': '2026-05-05T12:00:00',
                },
            ]
        raise KeyError(type(query).__name__)


class FakeContainer:
    def resolve(self, cls):
        if cls is Mediator:
            return FakeMediator()
        raise KeyError(cls)


def test_command_audit_endpoint_returns_records(monkeypatch):
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer())
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get(
        '/telescopes/commands/audit',
        params={'limit': 10, 'operation': 'set-tracking', 'status': 'ok', 'source': 'main-backend'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]['operation'] == 'set-tracking'
