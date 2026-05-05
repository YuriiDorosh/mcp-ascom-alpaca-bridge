from pydantic import BaseModel
from pydantic import Field


class AlpacaLiveStatusSchema(BaseModel):
    reachable: bool
    connected: bool | None = None
    tracking: bool | None = None
    device_name: str | None = None
    error_hint: str | None = None


class TelescopeStatusSchema(BaseModel):
    oid: str
    name: str
    connection_state: str
    tracking_enabled: bool
    created_at: str
    alpaca_live: AlpacaLiveStatusSchema | None = None


class RadecToAltAzRequestSchema(BaseModel):
    ra_hours: float = Field(ge=0, lt=24, description='ICRS right ascension in decimal hours.')
    dec_degrees: float = Field(ge=-90, le=90, description='ICRS declination in degrees.')
    latitude_deg: float = Field(ge=-90, le=90)
    longitude_deg: float = Field(ge=-180, le=180)
    elevation_m: float = Field(default=0, ge=-430, le=9000)
    obstime_utc_iso: str = Field(description='UTC time string that Astropy can parse (ISO-8601 recommended).')


class HorizontalCoordsResponseSchema(BaseModel):
    altitude_deg: float
    azimuth_deg: float
    obstime_utc: str


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
