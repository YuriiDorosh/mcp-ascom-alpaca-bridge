from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


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


class OperatorLiveViewSchema(BaseModel):
    """HTTP contract for operator FOV / still-frame preview (incremental rollout)."""

    schema_version: str = 'v1'
    available: bool = False
    provider: Literal['none', 'alpaca_camera', 'http_still', 'seestar_vendor', 'mjpeg'] = 'none'
    image_url: str | None = Field(
        default=None,
        description='When set, a URL the browser may load for a still or stream endpoint on the LAN.',
    )
    notes: str = Field(description='Human-readable status and integration notes for operators.')


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


class MountIcrsEquatorialSchema(BaseModel):
    """Instantaneous Alpaca telescope equatorial axes (hours / degrees), same numeric story as slew targets."""

    ra_hours: float = Field(description='Right ascension in decimal hours reported by the mount driver.')
    dec_degrees: float = Field(description='Declination in degrees reported by the mount driver.')
    frame: Literal['mount-equatorial-driver'] = Field(
        default='mount-equatorial-driver',
        description='Coordinate frame identifier; aligns with Alpaca SlewToCoordinates units.',
    )


class NudgeEquatorialRequestSchema(BaseModel):
    """Relative bump in sidereal RA seconds (east-positive) and declination arcseconds (north-positive).

    Larger bounds than early Alpaca stubs: ΔRA ±12 sidereal hours is ≈±180° at the celestial equator
    (ΔRA_hours×15°). ΔDec ±180° in arcseconds is clamped downstream to the mount poles (±90°).
    """

    delta_ra_sidereal_seconds: float = Field(
        ge=-43_200,
        le=43_200,
        description=(
            'RA offset as sidereal-time seconds; ΔRA_hours = Δ/3600 wraps in [0h,24h). '
            '|Δ|≤43200s is twelve sidereal hours (≈180° sky motion along RA at δ≈0).'
        ),
    )
    delta_dec_arcseconds: float = Field(
        ge=-648_000,
        le=648_000,
        description=(
            'Declination offset in arcseconds mapped to ΔDec_degrees = Δ/3600; handler clamps ±90°. '
            '|Δ|≤648000″ allows up to ±180° before clamping prevents impossible latitudes.'
        ),
    )

    @model_validator(mode='after')
    def deltas_not_all_zero(self) -> 'NudgeEquatorialRequestSchema':
        """Reject no-op payloads (common when SPA preset is ΔRA-only or ΔDec-only and user presses mixed axes)."""

        if abs(float(self.delta_ra_sidereal_seconds)) < 1e-12 and abs(float(self.delta_dec_arcseconds)) < 1e-12:
            raise ValueError(
                'Both deltas are zero; use a preset with ΔRA≠0 before East/West or ΔDec≠0 before North/South.',
            )
        return self


class NudgeEquatorialAckSchema(BaseModel):
    status: Literal['ok'] = 'ok'
    prior_ra_hours: float
    prior_dec_degrees: float
    target_ra_hours: float
    target_dec_degrees: float
    delta_ra_sidereal_seconds: float
    delta_dec_arcseconds: float


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


class SiteWeatherObservationSchema(BaseModel):
    """Portable surface-ish snapshot aligned with MCP context payloads (OpenWeather-backed today)."""

    schema_version: str = 'v1'
    provider: Literal['openweather']
    latitude: float
    longitude: float
    fetched_at_utc: str
    conditions_summary: str | None = None
    temperature_celsius: float | None = None
    cloud_cover_percent: float | None = None
    relative_humidity_percent: float | None = None
    wind_speed_m_per_s: float | None = None
    wind_direction_degrees: float | None = None
    visibility_meters: float | None = None
    surface_pressure_hpa: float | None = None


class McpContextWarningSchema(BaseModel):
    source: Literal['catalog', 'ephemeris', 'status', 'weather']
    code: str
    message: str


class TelescopeMcpContextSchema(BaseModel):
    capabilities: TelescopeCapabilitiesSchema
    telescope_status: TelescopeStatusSchema | None = None
    catalog_target: ResolvedCatalogIcrsSchema | None = None
    ephemeris_target: EphemerisIcrsResponseSchema | None = None
    weather_observation: SiteWeatherObservationSchema | None = None
    weather_advisories: list[str] = []
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


class McpExecutionPlanStepSchema(BaseModel):
    step: int
    tool_name: str
    purpose: str
    enabled: bool
    skip_reason: str | None = None


class TelescopeHardwareReadinessSchema(BaseModel):
    schema_version: str
    requires_real_telescope_now: bool
    trigger_task_id: str
    operator_action: str
    note: str


class TelescopeHardwareSmokePlanStepSchema(BaseModel):
    step: int
    action: str
    expected_result: str


class TelescopeHardwareSmokePlanSchema(BaseModel):
    schema_version: str
    trigger_task_id: str
    prerequisite: str
    steps: list[TelescopeHardwareSmokePlanStepSchema]


class TelescopeHardwareValidationPlanStepSchema(BaseModel):
    step: int
    action: str
    expected_result: str


class TelescopeHardwareValidationPlanSchema(BaseModel):
    schema_version: str
    trigger_task_id: str
    prerequisite: str
    steps: list[TelescopeHardwareValidationPlanStepSchema]


class TelescopeHardwareOverviewSchema(BaseModel):
    readiness: TelescopeHardwareReadinessSchema
    smoke_plan: TelescopeHardwareSmokePlanSchema
    validation_plan: TelescopeHardwareValidationPlanSchema


class McpExecutionPlanAppliedFiltersSchema(BaseModel):
    include_disabled_commands: bool


class McpExecutionPlanStatsSchema(BaseModel):
    baseline_steps: int
    returned_steps: int
    filtered_out_steps: int


class TelescopeMcpExecutionPlanSchema(BaseModel):
    objective: str
    mode: Literal['async', 'sync']
    applied_filters: McpExecutionPlanAppliedFiltersSchema
    stats: McpExecutionPlanStatsSchema
    hardware_readiness: TelescopeHardwareReadinessSchema
    hardware_smoke_plan: TelescopeHardwareSmokePlanSchema
    hardware_validation_plan: TelescopeHardwareValidationPlanSchema
    hardware_overview: TelescopeHardwareOverviewSchema
    steps: list[McpExecutionPlanStepSchema]


class TelescopeMcpBootstrapSchema(BaseModel):
    manifest: TelescopeMcpToolManifestSchema
    effective_manifest: TelescopeEffectiveMcpToolManifestSchema
    planning_guide: TelescopeMcpPlanningGuideSchema
    hardware_readiness: TelescopeHardwareReadinessSchema
    hardware_smoke_plan: TelescopeHardwareSmokePlanSchema
    hardware_validation_plan: TelescopeHardwareValidationPlanSchema
    hardware_overview: TelescopeHardwareOverviewSchema


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
