from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.api.telescope import handlers as telescope_handlers
from application.api.telescope.handlers import router as telescope_router
from domain.exceptions.telescope import WeatherDisabledException
from logic.mediator.base import Mediator
from logic.queries.weather import GetSiteWeatherObservationQuery
from settings.config import Config


class FakeMediatorWeather(Mediator):
    async def handle_query(self, query):
        if isinstance(query, GetSiteWeatherObservationQuery):
            return {
                'schema_version': 'v1',
                'provider': 'openweather',
                'latitude': query.latitude,
                'longitude': query.longitude,
                'fetched_at_utc': '2026-05-10T15:30:00Z',
                'conditions_summary': 'overcast clouds',
                'temperature_celsius': 17.8,
                'cloud_cover_percent': 88,
                'relative_humidity_percent': 62,
                'wind_speed_m_per_s': 4.8,
                'wind_direction_degrees': None,
                'visibility_meters': 8000,
                'surface_pressure_hpa': 1009,
            }
        raise AssertionError(query)

    async def handle_command(self, command):
        raise NotImplementedError


class WeatherDisabledMediator(Mediator):
    async def handle_query(self, query):
        if isinstance(query, GetSiteWeatherObservationQuery):
            raise WeatherDisabledException()
        raise AssertionError(query)

    async def handle_command(self, command):
        raise NotImplementedError


class FakeWeatherContainer:
    def __init__(self, mediator: Mediator):
        self._mediator = mediator

    def resolve(self, cls):
        if cls is Config:
            return Config(COMMAND_AUTH_TOKEN='')
        if cls is Mediator:
            return self._mediator
        raise KeyError(cls)


def test_site_weather_current_returns_normalized_payload(monkeypatch):
    monkeypatch.setattr(
        telescope_handlers,
        'init_container',
        lambda: FakeWeatherContainer(FakeMediatorWeather()),
    )

    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/weather/current', params={'latitude': 52.3676, 'longitude': 4.9041})
    assert response.status_code == 200
    body = response.json()
    assert body['provider'] == 'openweather'
    assert body['latitude'] == 52.3676
    assert body['longitude'] == 4.9041
    assert body['cloud_cover_percent'] == 88


def test_site_weather_returns_503_when_adapter_disabled(monkeypatch):
    monkeypatch.setattr(
        telescope_handlers,
        'init_container',
        lambda: FakeWeatherContainer(WeatherDisabledMediator()),
    )

    app = FastAPI()
    app.include_router(telescope_router, prefix='/telescopes')
    client = TestClient(app)

    response = client.get('/telescopes/weather/current', params={'latitude': 0.0, 'longitude': 0.0})
    assert response.status_code == 503
