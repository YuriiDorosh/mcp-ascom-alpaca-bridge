from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from logic.mediator.base import Mediator
from logic.queries.model_inference import GetModelInferenceResultQuery


class MappingMediator:
    def __init__(self, mapping: dict[str, dict | None]):
        self._mapping = mapping

    async def handle_query(self, query):
        if not isinstance(query, GetModelInferenceResultQuery):
            raise KeyError(type(query).__name__)
        return self._mapping.get(query.request_id)


class FakeContainer:
    def __init__(self, mediator):
        self._mediator = mediator

    def resolve(self, cls):
        if cls is Mediator:
            return self._mediator
        raise KeyError(cls)


def _client_for(monkeypatch, mapping: dict[str, dict | None]) -> TestClient:
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(MappingMediator(mapping)))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    return TestClient(app)


def test_model_inference_status_pending(monkeypatch):
    client = _client_for(monkeypatch, {'req-pending': None})
    response = client.get('/telescopes/model/inference/req-pending/status')
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        'request_id': 'req-pending',
        'status': 'pending',
        'result': None,
    }


def test_model_inference_status_completed(monkeypatch):
    client = _client_for(
        monkeypatch,
        {
            'req-done': {
                'request_id': 'req-done',
                'status': 'completed',
                'output_text': 'ok',
                'error_message': None,
                'finished_at': '2026-05-06T04:00:00',
            },
        },
    )
    response = client.get('/telescopes/model/inference/req-done/status')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'completed'
    assert payload['result']['request_id'] == 'req-done'


def test_model_inference_status_failed(monkeypatch):
    client = _client_for(
        monkeypatch,
        {
            'req-failed': {
                'request_id': 'req-failed',
                'status': 'failed',
                'output_text': None,
                'error_message': 'runtime error',
                'finished_at': '2026-05-06T04:00:00',
            },
        },
    )
    response = client.get('/telescopes/model/inference/req-failed/status')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'failed'
    assert payload['result']['error_message'] == 'runtime error'
