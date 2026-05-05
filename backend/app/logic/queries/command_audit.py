from dataclasses import dataclass

from infra.repositories.operations.base import BaseModelInferenceRepository
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


@dataclass(frozen=True)
class ListCommandAuditQuery(BaseQuery):
    limit: int = 50


@dataclass(frozen=True)
class ListCommandAuditQueryHandler(BaseQueryHandler[ListCommandAuditQuery, list[dict]]):
    repository: BaseModelInferenceRepository

    async def handle(self, query: ListCommandAuditQuery) -> list[dict]:
        normalized_limit = min(max(query.limit, 1), 200)
        return await self.repository.list_command_audits(limit=normalized_limit)
