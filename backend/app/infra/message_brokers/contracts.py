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
