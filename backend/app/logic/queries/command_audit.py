from dataclasses import dataclass

from infra.repositories.operations.base import BaseModelInferenceRepository
from logic.queries.base import (
    BaseQuery,
    BaseQueryHandler,
)


@dataclass(frozen=True)
class ListCommandAuditQuery(BaseQuery):
    limit: int = 50
    operation: str | None = None
    status: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class ListCommandAuditQueryHandler(BaseQueryHandler[ListCommandAuditQuery, list[dict]]):
    repository: BaseModelInferenceRepository

    async def handle(self, query: ListCommandAuditQuery) -> list[dict]:
        normalized_limit = min(max(query.limit, 1), 200)
        operation = query.operation.strip() if query.operation else None
        status = query.status.strip() if query.status else None
        source = query.source.strip() if query.source else None
        return await self.repository.list_command_audits(
            limit=normalized_limit,
            operation=operation,
            status=status,
            source=source,
        )
