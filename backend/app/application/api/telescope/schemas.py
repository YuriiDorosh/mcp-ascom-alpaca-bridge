from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class AlpacaLiveStatusSchema(BaseModel):
    reachable: bool
    connected: bool | None = None
    tracking: bool | None = None
    supports_slew: bool | None = None
    supports_sync: bool | None = None
    supports_tracking: bool | None = None
    device_name: str | None = None
    error_hint: str | None = None


class TelescopeCapabilitiesSchema(BaseModel):
    supports_slew: bool
    supports_sync: bool
    supports_tracking: bool
    source: Literal['alpaca-live', 'default-disabled']


class TelescopeStatusSchema(BaseModel):
    oid: str
    name: str
    connection_state: str
    tracking_enabled: bool
    created_at: str
    alpaca_live: AlpacaLiveStatusSchema | None = None
    capabilities: TelescopeCapabilitiesSchema


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


class IcrsHourAngleDecSchema(BaseModel):
    ra_hours: float = Field(ge=0, lt=24)
    dec_degrees: float = Field(ge=-90, le=90)


class TelescopeCommandAckSchema(BaseModel):
    status: Literal['ok'] = 'ok'


class CommandAuditRecordSchema(BaseModel):
    audit_id: str
    operation: str
    status: str
    details: dict
    source: str
    recorded_at: str


class ResolvedCatalogIcrsSchema(BaseModel):
    designation: str
    ra_hours: float
    dec_degrees: float


class EphemerisIcrsResponseSchema(BaseModel):
    body: str
    obstime_utc: str
    ra_hours: float
    dec_degrees: float


class McpContextWarningSchema(BaseModel):
    source: Literal['catalog', 'ephemeris', 'status']
    code: str
    message: str


class TelescopeMcpContextSchema(BaseModel):
    capabilities: TelescopeCapabilitiesSchema
    telescope_status: TelescopeStatusSchema | None = None
    catalog_target: ResolvedCatalogIcrsSchema | None = None
    ephemeris_target: EphemerisIcrsResponseSchema | None = None
    warnings: list[McpContextWarningSchema] = []


class McpToolRequirementSchema(BaseModel):
    required_capability: Literal['supports_slew', 'supports_sync', 'supports_tracking'] | None = None
    requires_command_token: bool = False


class McpToolManifestItemSchema(BaseModel):
    tool_name: str
    description: str
    method: Literal['GET', 'POST']
    endpoint: str
    requirements: McpToolRequirementSchema


class TelescopeMcpToolManifestSchema(BaseModel):
    tools: list[McpToolManifestItemSchema]


class EffectiveMcpToolManifestItemSchema(McpToolManifestItemSchema):
    enabled: bool
    disabled_reason: str | None = None


class TelescopeEffectiveMcpToolManifestSchema(BaseModel):
    tools: list[EffectiveMcpToolManifestItemSchema]


class McpInferenceFlowStepSchema(BaseModel):
    step: int
    tool_name: str
    purpose: str
    when_to_use: str


class McpInferenceTimeoutPolicySchema(BaseModel):
    default_timeout_seconds: float
    max_timeout_seconds: float
    default_poll_interval_seconds: float
    max_poll_interval_seconds: float


class TelescopeMcpPlanningGuideSchema(BaseModel):
    objective: str
    safety_notes: list[str]
    inference_flow: list[McpInferenceFlowStepSchema]
    timeout_policy: McpInferenceTimeoutPolicySchema


class TelescopeMcpBootstrapSchema(BaseModel):
    manifest: TelescopeMcpToolManifestSchema
    planning_guide: TelescopeMcpPlanningGuideSchema


class SetTelescopeTrackingRequestSchema(BaseModel):
    enabled: bool


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


class ModelInferenceStatusSchema(BaseModel):
    request_id: str
    status: Literal['pending', 'completed', 'failed']
    result: ModelInferenceResultSchema | None = None
