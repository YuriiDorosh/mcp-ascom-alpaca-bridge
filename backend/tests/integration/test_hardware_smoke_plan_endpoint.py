from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope.handlers import router as telescope_router


def test_hardware_smoke_plan_exposes_machine_readable_steps():
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/hardware/smoke-plan')
    assert response.status_code == 200
    payload = response.json()

    assert payload['trigger_task_id'] == 'P5-HW-SMOKE'
    assert 'Charge Seestar S30 Pro' in payload['prerequisite']
    assert isinstance(payload['steps'], list)
    assert len(payload['steps']) >= 4
    first = payload['steps'][0]
    assert first['step'] == 1
    assert 'GET /telescopes/status' in first['action']
    assert 'capability flags' in first['expected_result']
