from dataclasses import dataclass

from domain.ports.weather_observation import IWeatherObservationService
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


@dataclass(frozen=True)
class GetSiteWeatherObservationQuery(BaseQuery):
    latitude: float
    longitude: float


@dataclass(frozen=True)
class GetSiteWeatherObservationHandler(BaseQueryHandler[GetSiteWeatherObservationQuery, dict]):
    observation: IWeatherObservationService

    async def handle(self, query: GetSiteWeatherObservationQuery) -> dict:
        return await self.observation.fetch_current_observation(
            latitude=query.latitude,
            longitude=query.longitude,
        )
