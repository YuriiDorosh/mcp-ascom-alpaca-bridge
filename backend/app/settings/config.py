from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        protected_namespaces=('settings_',),
    )
    mongodb_connection_uri: str = Field(default='mongodb://localhost:27017', alias='MONGO_DB_CONNECTION_URI')
    mongodb_database: str = Field(default='alpaca_astro_center', alias='MONGODB_DATABASE')
    mongodb_telescope_collection: str = Field(default='telescopes', alias='MONGODB_TELESCOPE_COLLECTION')
    mongodb_operation_collection: str = Field(default='operations', alias='MONGODB_OPERATION_COLLECTION')

    telescope_status_topic: str = Field(default='telescope-status')
    telescope_operation_topic: str = Field(default='telescope-operation-events', alias='TELESCOPE_OPERATION_TOPIC')
    model_inference_request_topic: str = Field(default='model-inference-request')
    model_inference_result_topic: str = Field(default='model-inference-result')

    kafka_url: str = Field(default='localhost:9092', alias='KAFKA_URL')

    alpaca_enabled: bool = Field(default=False, alias='ALPACA_ENABLED')
    alpaca_address: str = Field(default='127.0.0.1:11111', alias='ALPACA_ADDRESS')
    alpaca_device_number: int = Field(default=0, alias='ALPACA_DEVICE_NUMBER')
    alpaca_protocol: str = Field(default='http', alias='ALPACA_PROTOCOL')
    alpaca_connect_timeout_seconds: float = Field(default=8.0, alias='ALPACA_CONNECT_TIMEOUT_SECONDS')

    catalog_lookup_enabled: bool = Field(default=False, alias='CATALOG_LOOKUP_ENABLED')
    catalog_resolve_timeout_seconds: float = Field(default=20.0, alias='CATALOG_RESOLVE_TIMEOUT_SECONDS')

    ephemeris_enabled: bool = Field(default=False, alias='EPHEMERIS_ENABLED')
    ephemeris_kernel: str = Field(default='de421.bsp', alias='EPHEMERIS_KERNEL')

    command_auth_token: str | None = Field(default=None, alias='COMMAND_AUTH_TOKEN')

    # Comma-separated browser origins for the Vite/React UI. None = default localhost dev ports; '' disables CORS middleware.
    cors_allowed_origins: str | None = Field(default=None, alias='CORS_ALLOWED_ORIGINS')
