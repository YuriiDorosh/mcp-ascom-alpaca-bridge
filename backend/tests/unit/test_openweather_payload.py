from infra.integrations.openweather.observation import OpenWeatherObservationService
from settings.config import Config


def test_openweather_normalizer_handles_full_payload():
    service = OpenWeatherObservationService(Config(WEATHER_PROVIDER='openweather', OPENWEATHER_API_KEY='secret'))
    out = service._normalize_payload(
        latitude=50.4,
        longitude=30.5,
        payload={
            'dt': 1715000123,
            'weather': [{'description': 'Light Rain', 'main': 'Rain'}],
            'clouds': {'all': 92},
            'main': {'temp': 14.2, 'humidity': 71, 'pressure': 1003},
            'wind': {'speed': 11.8, 'deg': 215},
            'visibility': 4200,
        },
    )
    assert out['provider'] == 'openweather'
    assert out['cloud_cover_percent'] == 92
    assert out['wind_speed_m_per_s'] == 11.8
    assert out['conditions_summary'] == 'light rain'
    assert out['visibility_meters'] == 4200
