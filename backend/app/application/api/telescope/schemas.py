from pydantic import BaseModel


class TelescopeStatusSchema(BaseModel):
    oid: str
    name: str
    connection_state: str
    tracking_enabled: bool
    created_at: str


class ModelInferenceRequestSchema(BaseModel):
    prompt: str


class ModelInferenceEnqueuedSchema(BaseModel):
    request_id: str
    topic: str


class ModelInferenceResultSchema(BaseModel):
    request_id: str
    status: str
    output_text: str | None = None
    error_message: str | None = None
    finished_at: str
