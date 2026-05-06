from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope.handlers import router as telescope_router


def test_mcp_planning_guide_exposes_inference_sequence_and_timeout_policy():
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/tools/mcp-planning-guide')
    assert response.status_code == 200
    payload = response.json()

    assert payload['objective']
    assert len(payload['safety_notes']) >= 2

    steps = payload['inference_flow']
    assert [step['tool_name'] for step in steps] == [
        'model.enqueue_inference',
        'model.get_inference_status',
        'model.wait_inference_result',
        'model.enqueue_and_wait_inference',
    ]

    timeout_policy = payload['timeout_policy']
    assert timeout_policy['default_timeout_seconds'] == 15.0
    assert timeout_policy['max_timeout_seconds'] == 60.0
    assert timeout_policy['default_poll_interval_seconds'] == 0.5
    assert timeout_policy['max_poll_interval_seconds'] == 2.0
