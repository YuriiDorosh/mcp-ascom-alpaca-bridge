from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass(frozen=True)
class ModelInferenceRequestContract:
    request_id: str
    prompt: str
    created_at: str
    source: str = 'main-backend'

    @classmethod
    def create(cls, prompt: str) -> 'ModelInferenceRequestContract':
        return cls(
            request_id=str(uuid4()),
            prompt=prompt,
            created_at=datetime.now().isoformat(),
        )


@dataclass(frozen=True)
class ModelInferenceResultContract:
    request_id: str
    status: str
    output_text: str | None
    error_message: str | None
    finished_at: str


@dataclass(frozen=True)
class TelescopeStatusContract:
    telescope_oid: str
    connection_state: str
    tracking_enabled: bool
    published_at: str


@dataclass(frozen=True)
class TelescopeOperationEventContract:
    event_id: str
    operation: str
    status: str
    target_ra_hours: float | None
    target_dec_degrees: float | None
    tracking_enabled: bool | None
    occurred_at: str
    source: str = 'main-backend'

    @classmethod
    def create(
        cls,
        *,
        operation: str,
        status: str = 'ok',
        target_ra_hours: float | None = None,
        target_dec_degrees: float | None = None,
        tracking_enabled: bool | None = None,
    ) -> 'TelescopeOperationEventContract':
        return cls(
            event_id=str(uuid4()),
            operation=operation,
            status=status,
            target_ra_hours=target_ra_hours,
            target_dec_degrees=target_dec_degrees,
            tracking_enabled=tracking_enabled,
            occurred_at=datetime.now().isoformat(),
        )
