from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope.handlers import router as telescope_router


def test_hardware_readiness_exposes_phase5_trigger():
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/hardware/readiness')
    assert response.status_code == 200
    payload = response.json()

    assert payload['requires_real_telescope_now'] is False
    assert payload['trigger_task_id'] == 'P5-HW-SMOKE'
    assert 'Charge and prepare Seestar S30 Pro' in payload['operator_action']
