import pytest

from application.api.lifespan import consume_model_inference_results


class FakeBroker:
    def __init__(self, payloads):
        self._payloads = payloads

    async def start_consuming(self, topic: str):
        for payload in self._payloads:
            yield payload


class FakeRepository:
    def __init__(self):
        self._store = {}
        self.saved = []

    async def get_by_request_id(self, request_id: str):
        return self._store.get(request_id)

    async def save_result(self, request_id: str, status: str, output_text: str | None, error_message: str | None, finished_at: str):
        doc = {
            'request_id': request_id,
            'status': status,
            'output_text': output_text,
            'error_message': error_message,
            'finished_at': finished_at,
        }
        self._store[request_id] = doc
        self.saved.append(doc)
        return doc


class FakeConfig:
    model_inference_result_topic = 'model-inference-result'


class FakeContainer:
    def __init__(self, broker: FakeBroker, repo: FakeRepository):
        self._broker = broker
        self._repo = repo
        self._config = FakeConfig()

    def resolve(self, cls):
        from infra.message_brokers.base import BaseMessageBroker
        from infra.repositories.operations.base import BaseModelInferenceRepository
        from settings.config import Config

        if cls is BaseMessageBroker:
            return self._broker
        if cls is BaseModelInferenceRepository:
            return self._repo
        if cls is Config:
            return self._config
        raise KeyError(cls)


@pytest.mark.asyncio
async def test_consumer_skips_exact_duplicate_model_inference_payload(monkeypatch):
    payload = {
        'schema_version': 'v1',
        'request_id': 'req-1',
        'correlation_id': 'req-1',
        'status': 'completed',
        'output_text': 'answer',
        'error_message': None,
        'finished_at': '2026-05-05T12:00:00',
    }
    broker = FakeBroker([payload, payload.copy()])
    repo = FakeRepository()
    monkeypatch.setattr('application.api.lifespan.init_container', lambda: FakeContainer(broker, repo))

    await consume_model_inference_results()

    assert len(repo.saved) == 1
    assert repo.saved[0]['request_id'] == 'req-1'
