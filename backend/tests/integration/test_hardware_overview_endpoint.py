from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope.handlers import router as telescope_router


def test_hardware_overview_aggregates_readiness_and_both_plans():
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/hardware/overview')
    assert response.status_code == 200
    payload = response.json()

    readiness = payload['readiness']
    smoke_plan = payload['smoke_plan']
    validation_plan = payload['validation_plan']

    assert readiness['schema_version'] == 'v1'
    assert readiness['trigger_task_id'] == 'P5-HW-SMOKE'
    assert smoke_plan['trigger_task_id'] == 'P5-HW-SMOKE'
    assert validation_plan['trigger_task_id'] == 'P5-HW-VALIDATION'
    assert len(smoke_plan['steps']) >= 4
    assert len(validation_plan['steps']) >= 4


def test_hardware_overview_matches_individual_hardware_contract_endpoints():
    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    overview_response = client.get('/telescopes/hardware/overview')
    readiness_response = client.get('/telescopes/hardware/readiness')
    smoke_response = client.get('/telescopes/hardware/smoke-plan')
    validation_response = client.get('/telescopes/hardware/validation-plan')

    assert overview_response.status_code == 200
    assert readiness_response.status_code == 200
    assert smoke_response.status_code == 200
    assert validation_response.status_code == 200

    overview = overview_response.json()
    assert overview['readiness'] == readiness_response.json()
    assert overview['smoke_plan'] == smoke_response.json()
    assert overview['validation_plan'] == validation_response.json()
