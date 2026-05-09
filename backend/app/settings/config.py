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
    # Async slew (Alpaca / ITelescope): poll Slewing until False after SlewToCoordinatesAsync.
    alpaca_slew_timeout_seconds: float = Field(default=420.0, ge=5.0, alias='ALPACA_SLEW_TIMEOUT_SECONDS')
    alpaca_slew_poll_interval_seconds: float = Field(default=0.25, gt=0, le=5.0, alias='ALPACA_SLEW_POLL_INTERVAL_SECONDS')

    catalog_lookup_enabled: bool = Field(default=False, alias='CATALOG_LOOKUP_ENABLED')
    catalog_resolve_timeout_seconds: float = Field(default=20.0, alias='CATALOG_RESOLVE_TIMEOUT_SECONDS')

    ephemeris_enabled: bool = Field(default=False, alias='EPHEMERIS_ENABLED')
    ephemeris_kernel: str = Field(default='de421.bsp', alias='EPHEMERIS_KERNEL')

    command_auth_token: str | None = Field(default=None, alias='COMMAND_AUTH_TOKEN')

    # Comma-separated browser origins for the Vite/React UI. None = default localhost dev ports; '' disables CORS middleware.
    cors_allowed_origins: str | None = Field(default=None, alias='CORS_ALLOWED_ORIGINS')

    # Optional absolute http(s) URL for operator FOV still/MJPEG; exposed via GET /telescopes/operator/live-view.
    operator_live_view_image_url: str | None = Field(default=None, alias='OPERATOR_LIVE_VIEW_IMAGE_URL')

    # RTSP telescope camera relay (JPEG over multipart MJPEG HTTP). Leave unset to disable /api/v1/telescope/stream.
    telescope_rtsp_url: str | None = Field(default=None, alias='TELESCOPE_RTSP_URL')
    telescope_rtsp_transport_tcp: bool = Field(default=True, alias='TELESCOPE_RTSP_TRANSPORT_TCP')
    # Downscale frames when wider than this (aspect preserved); None keeps the camera-native size.
    telescope_rtsp_max_frame_width: int | None = Field(default=None, alias='TELESCOPE_RTSP_MAX_FRAME_WIDTH')
    telescope_rtsp_jpeg_quality: int = Field(default=80, ge=1, le=100, alias='TELESCOPE_RTSP_JPEG_QUALITY')
    telescope_rtsp_reconnect_initial_seconds: float = Field(default=0.5, gt=0, alias='TELESCOPE_RTSP_RECONNECT_INITIAL')
    telescope_rtsp_reconnect_max_seconds: float = Field(default=5.0, gt=0, alias='TELESCOPE_RTSP_RECONNECT_MAX')
