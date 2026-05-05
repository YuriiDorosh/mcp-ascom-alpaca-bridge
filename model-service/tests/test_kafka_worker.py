from app.kafka_worker import KafkaInferenceWorker
from app.settings import Config


def test_build_result_contract_completed_for_valid_prompt():
    worker = KafkaInferenceWorker(Config(MODEL_WORKER_ENABLED=False))
    payload = {
        'schema_version': 'v1',
        'request_id': 'req-1',
        'correlation_id': 'corr-1',
        'prompt': 'hello sky',
        'created_at': '2026-05-05T12:00:00',
        'source': 'main-backend',
    }

    result = worker._build_result_contract(payload)
    assert result.status == 'completed'
    assert result.request_id == 'req-1'
    assert result.correlation_id == 'corr-1'
    assert result.error_message is None
    assert result.output_text is not None


def test_build_result_contract_failed_when_runtime_raises(monkeypatch):
    worker = KafkaInferenceWorker(Config(MODEL_WORKER_ENABLED=False))
    payload = {
        'schema_version': 'v1',
        'request_id': 'req-2',
        'prompt': 'broken prompt',
        'created_at': '2026-05-05T12:00:00',
    }

    def _raise(*args, **kwargs):
        raise RuntimeError('model runtime boom')

    monkeypatch.setattr('app.kafka_worker.run_inference', _raise)

    result = worker._build_result_contract(payload)
    assert result.status == 'failed'
    assert result.request_id == 'req-2'
    assert result.correlation_id == 'req-2'
    assert result.output_text is None
    assert result.error_message == 'model runtime boom'
