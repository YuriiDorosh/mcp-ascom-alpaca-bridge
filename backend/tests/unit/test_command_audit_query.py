import pytest

from logic.queries.command_audit import (
    ListCommandAuditQuery,
    ListCommandAuditQueryHandler,
)


class FakeAuditRepository:
    def __init__(self):
        self.last_limit = None

    async def list_command_audits(self, *, limit: int = 50) -> list[dict]:
        self.last_limit = limit
        return [{'audit_id': 'a1', 'operation': 'slew-icrs', 'status': 'ok', 'details': {}, 'source': 'main-backend', 'recorded_at': '2026-05-05T12:00:00'}]


@pytest.mark.asyncio
async def test_list_command_audit_query_handler_normalizes_limit():
    repo = FakeAuditRepository()
    handler = ListCommandAuditQueryHandler(repository=repo)  # type: ignore[arg-type]

    await handler.handle(ListCommandAuditQuery(limit=999))
    assert repo.last_limit == 200

    await handler.handle(ListCommandAuditQuery(limit=-5))
    assert repo.last_limit == 1
