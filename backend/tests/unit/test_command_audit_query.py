import pytest

from logic.queries.command_audit import (
    ListCommandAuditQuery,
    ListCommandAuditQueryHandler,
)


class FakeAuditRepository:
    def __init__(self):
        self.last_limit = None
        self.last_operation = None
        self.last_status = None
        self.last_source = None

    async def list_command_audits(
        self,
        *,
        limit: int = 50,
        operation: str | None = None,
        status: str | None = None,
        source: str | None = None,
    ) -> list[dict]:
        self.last_limit = limit
        self.last_operation = operation
        self.last_status = status
        self.last_source = source
        return [{'audit_id': 'a1', 'operation': 'slew-icrs', 'status': 'ok', 'details': {}, 'source': 'main-backend', 'recorded_at': '2026-05-05T12:00:00'}]


@pytest.mark.asyncio
async def test_list_command_audit_query_handler_normalizes_limit():
    repo = FakeAuditRepository()
    handler = ListCommandAuditQueryHandler(repository=repo)  # type: ignore[arg-type]

    await handler.handle(ListCommandAuditQuery(limit=999))
    assert repo.last_limit == 200

    await handler.handle(ListCommandAuditQuery(limit=-5))
    assert repo.last_limit == 1


@pytest.mark.asyncio
async def test_list_command_audit_query_handler_passes_filters():
    repo = FakeAuditRepository()
    handler = ListCommandAuditQueryHandler(repository=repo)  # type: ignore[arg-type]

    await handler.handle(
        ListCommandAuditQuery(
            limit=10,
            operation='  slew-icrs ',
            status=' ok ',
            source=' main-backend ',
        ),
    )
    assert repo.last_operation == 'slew-icrs'
    assert repo.last_status == 'ok'
    assert repo.last_source == 'main-backend'
