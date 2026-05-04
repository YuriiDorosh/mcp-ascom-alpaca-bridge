from dataclasses import dataclass

from infra.repositories.operations.base import BaseModelInferenceRepository
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


@dataclass(frozen=True)
class GetModelInferenceResultQuery(BaseQuery):
    request_id: str


@dataclass(frozen=True)
class GetModelInferenceResultQueryHandler(BaseQueryHandler[GetModelInferenceResultQuery, dict | None]):
    repository: BaseModelInferenceRepository

    async def handle(self, query: GetModelInferenceResultQuery) -> dict | None:
        return await self.repository.get_by_request_id(query.request_id)
