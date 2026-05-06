from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from logic.commands.model_inference import EnqueueModelInferenceCommand
from logic.mediator.base import Mediator
from logic.queries.model_inference import GetModelInferenceResultQuery


class FakeMediator:
    def __init__(self, query_sequence: list[dict | None]):
        self._query_sequence = query_sequence
        self._idx = 0

    async def handle_command(self, command):
        if not isinstance(command, EnqueueModelInferenceCommand):
            raise KeyError(type(command).__name__)
        return [{'request_id': 'req-enqueued', 'topic': 'model-inference-request'}]

    async def handle_query(self, query):
        if not isinstance(query, GetModelInferenceResultQuery):
            raise KeyError(type(query).__name__)
        if self._idx >= len(self._query_sequence):
            return self._query_sequence[-1]
        value = self._query_sequence[self._idx]
        self._idx += 1
        return value


class FakeContainer:
    def __init__(self, mediator):
        self._mediator = mediator

    def resolve(self, cls):
        if cls is Mediator:
            return self._mediator
        raise KeyError(cls)


def test_enqueue_and_wait_returns_result(monkeypatch):
    mediator = FakeMediator(
        [
            None,
            {
                'request_id': 'req-enqueued',
                'status': 'completed',
                'output_text': 'hello',
                'error_message': None,
                'finished_at': '2026-05-06T01:00:00',
            },
        ],
    )
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(mediator))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.post(
        '/telescopes/model/inference/enqueue-and-wait',
        params={'timeout_seconds': 1, 'poll_interval_seconds': 0.01},
        json={'prompt': 'hello'},
    )
    assert response.status_code == 200
    assert response.json()['request_id'] == 'req-enqueued'


def test_enqueue_and_wait_times_out(monkeypatch):
    mediator = FakeMediator([None, None, None])
    monkeypatch.setattr(telescope_handlers, 'init_container', lambda: FakeContainer(mediator))
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.post(
        '/telescopes/model/inference/enqueue-and-wait',
        params={'timeout_seconds': 0.05, 'poll_interval_seconds': 0.01},
        json={'prompt': 'timeout'},
    )
    assert response.status_code == 504
    assert 'req-enqueued' in response.json()['detail']
