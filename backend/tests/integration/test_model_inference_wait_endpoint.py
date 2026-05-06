from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from logic.mediator.base import Mediator
from logic.queries.model_inference import GetModelInferenceResultQuery


class SequencedMediator:
    def __init__(self, sequence: list[dict | None]):
        self._sequence = sequence
        self._idx = 0

    async def handle_query(self, query):
        if not isinstance(query, GetModelInferenceResultQuery):
            raise KeyError(type(query).__name__)
        if self._idx >= len(self._sequence):
            return self._sequence[-1]
        value = self._sequence[self._idx]
        self._idx += 1
        return value


class FakeContainer:
    def __init__(self, mediator):
        self._mediator = mediator

    def resolve(self, cls):
        if cls is Mediator:
            return self._mediator
        raise KeyError(cls)


def test_wait_model_inference_result_returns_when_result_arrives(monkeypatch):
    mediator = SequencedMediator(
        [
            None,
            {
                'request_id': 'req-1',
                'status': 'completed',
                'output_text': 'ok',
                'error_message': None,
                'finished_at': '2026-05-06T01:00:00',
            },
        ],
    )
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(mediator))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get(
        '/telescopes/model/inference/req-1/wait',
        params={'timeout_seconds': 1, 'poll_interval_seconds': 0.01},
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'completed'


def test_wait_model_inference_result_times_out(monkeypatch):
    mediator = SequencedMediator([None, None, None])
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(mediator))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get(
        '/telescopes/model/inference/req-timeout/wait',
        params={'timeout_seconds': 0.05, 'poll_interval_seconds': 0.01},
    )
    assert response.status_code == 504
    assert 'timeout exceeded' in response.json()['detail']
