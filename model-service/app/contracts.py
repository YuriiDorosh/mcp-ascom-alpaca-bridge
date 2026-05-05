from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ModelInferenceRequestContract:
    schema_version: str
    request_id: str
    correlation_id: str
    prompt: str
    created_at: str
    source: str = 'main-backend'


@dataclass(frozen=True)
class ModelInferenceResultContract:
    schema_version: str
    request_id: str
    correlation_id: str
    status: str
    output_text: str | None
    error_message: str | None
    finished_at: str
    source: str = 'local-model-service'

    @classmethod
    def completed(
        cls,
        *,
        request_id: str,
        correlation_id: str,
        output_text: str,
        source: str,
    ) -> 'ModelInferenceResultContract':
        return cls(
            schema_version='v1',
            request_id=request_id,
            correlation_id=correlation_id,
            status='completed',
            output_text=output_text,
            error_message=None,
            finished_at=datetime.now().isoformat(),
            source=source,
        )
