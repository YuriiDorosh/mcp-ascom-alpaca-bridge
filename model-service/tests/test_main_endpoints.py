from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_includes_runtime_profiles():
    response = client.get('/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['runtime_profile'] in payload['supported_runtime_profiles']
    assert set(payload['supported_runtime_profiles']) == {'cpu', 'amd', 'nvidia'}


def test_runtime_profiles_endpoint_exposes_active_and_supported_profiles():
    response = client.get('/runtime/profiles')
    assert response.status_code == 200
    payload = response.json()
    assert payload['active_profile'] in payload['supported_profiles']
    assert set(payload['supported_profiles']) == {'cpu', 'amd', 'nvidia'}
