from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope.handlers import router as telescope_router


def test_hardware_validation_plan_exposes_machine_readable_steps():
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/hardware/validation-plan')
    assert response.status_code == 200
    payload = response.json()

    assert payload['schema_version'] == 'v1'
    assert payload['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert 'P5-HW-SMOKE' in payload['prerequisite']
    assert isinstance(payload['steps'], list)
    assert len(payload['steps']) >= 4
    first = payload['steps'][0]
    assert first['step'] == 1
    assert 'COMMAND_AUTH_TOKEN' in first['action']
    assert '401' in first['expected_result']
