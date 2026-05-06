from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

RuntimeProfile = Literal['cpu', 'amd', 'nvidia']
SUPPORTED_RUNTIME_PROFILES: tuple[RuntimeProfile, ...] = ('cpu', 'amd', 'nvidia')


class Config(BaseSettings):
    kafka_url: str = Field(default='localhost:9092', alias='KAFKA_URL')
    model_inference_request_topic: str = Field(default='model-inference-request', alias='MODEL_INFERENCE_REQUEST_TOPIC')
    model_inference_result_topic: str = Field(default='model-inference-result', alias='MODEL_INFERENCE_RESULT_TOPIC')
    model_runtime_profile: RuntimeProfile = Field(default='cpu', alias='MODEL_RUNTIME_PROFILE')
    model_worker_enabled: bool = Field(default=True, alias='MODEL_WORKER_ENABLED')
    model_service_source: str = Field(default='local-model-service', alias='MODEL_SERVICE_SOURCE')
