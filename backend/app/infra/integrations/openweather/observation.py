from datetime import UTC
from datetime import datetime

import httpx

from domain.exceptions.telescope import WeatherDisabledException
from domain.exceptions.telescope import WeatherUnavailableException
from domain.ports.weather_observation import IWeatherObservationService
from settings.config import Config


class OpenWeatherObservationService(IWeatherObservationService):
    """OpenWeather Current Weather API 2.5 (HTTPS, metric units)."""

    _URL = 'https://api.openweathermap.org/data/2.5/weather'

    def __init__(self, config: Config):
        self._config = config

    async def fetch_current_observation(self, *, latitude: float, longitude: float) -> dict:
        raw_provider = getattr(self._config, 'weather_provider', None)
        normalized = ((raw_provider or 'none').strip()).lower()
        if normalized != 'openweather':
            raise WeatherDisabledException()

        key = (self._config.openweather_api_key or '').strip()
        if not key:
            raise WeatherUnavailableException('OPENWEATHER_API_KEY is unset while WEATHER_PROVIDER=openweather.')

        timeout = max(2.0, float(self._config.openweather_timeout_seconds))
        params = {'lat': latitude, 'lon': longitude, 'units': 'metric', 'appid': key}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(self._URL, params=params)
        except httpx.TimeoutException as exc:
            raise WeatherUnavailableException('OpenWeather request timed out.') from exc
        except httpx.RequestError as exc:
            raise WeatherUnavailableException(f'OpenWeather HTTP error: {exc}') from exc

        if response.status_code == 401:
            raise WeatherUnavailableException('OpenWeather rejected the configured API key (401).')
        if response.status_code == 429:
            raise WeatherUnavailableException('OpenWeather rate limit hit (429).')
        if response.status_code >= 400:
            raise WeatherUnavailableException(
                f'OpenWeather upstream error ({response.status_code}): {(response.text or "")[:200]}',
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise WeatherUnavailableException('OpenWeather returned non-JSON.') from exc

        return self._normalize_payload(payload=payload, latitude=latitude, longitude=longitude)

    def _normalize_payload(self, *, payload: dict, latitude: float, longitude: float) -> dict:
        main = payload.get('main') or {}
        clouds = payload.get('clouds') or {}
        wind = payload.get('wind') or {}
        weather_stub = payload.get('weather')
        summary = None
        if isinstance(weather_stub, list) and weather_stub:
            first = weather_stub[0]
            if isinstance(first, dict):
                summary = first.get('description') or first.get('main')

        ts = payload.get('dt')
        if isinstance(ts, (int, float)):
            fetched = datetime.fromtimestamp(float(ts), tz=UTC).isoformat().replace('+00:00', 'Z')
        else:
            fetched = datetime.now(tz=UTC).isoformat().replace('+00:00', 'Z')

        vis = payload.get('visibility')
        visibility_meters = float(vis) if isinstance(vis, (int, float)) else None

        clouds_all = clouds.get('all')
        humidity = main.get('humidity')
        temp = main.get('temp')
        pressure = main.get('pressure')

        wind_speed = wind.get('speed')
        wind_deg = wind.get('deg')

        return {
            'schema_version': 'v1',
            'provider': 'openweather',
            'latitude': float(latitude),
            'longitude': float(longitude),
            'fetched_at_utc': fetched,
            'conditions_summary': str(summary).lower() if summary else None,
            'temperature_celsius': float(temp) if temp is not None else None,
            'cloud_cover_percent': float(clouds_all) if clouds_all is not None else None,
            'relative_humidity_percent': float(humidity) if humidity is not None else None,
            'wind_speed_m_per_s': float(wind_speed) if wind_speed is not None else None,
            'wind_direction_degrees': float(wind_deg) if wind_deg is not None else None,
            'visibility_meters': visibility_meters,
            'surface_pressure_hpa': float(pressure) if pressure is not None else None,
        }
