import asyncio
from typing import Annotated

from fastapi import APIRouter
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query

from domain.exceptions.infrastructure import InfrastructureUnavailableException
from domain.exceptions.telescope import AlpacaDriverException
from domain.exceptions.telescope import CatalogLookupDisabledException
from domain.exceptions.telescope import CatalogLookupTimeoutException
from domain.exceptions.telescope import CoordinateTransformException
from domain.exceptions.telescope import EphemerisDisabledException
from domain.exceptions.telescope import EphemerisUnavailableException
from domain.exceptions.telescope import UnresolvedObjectNameException
from application.api.telescope.schemas import (
    CommandAuditRecordSchema,
    EphemerisIcrsResponseSchema,
    HorizontalCoordsResponseSchema,
    IcrsHourAngleDecSchema,
    McpContextWarningSchema,
    ModelInferenceEnqueuedSchema,
    ModelInferenceResultSchema,
    ModelInferenceStatusSchema,
    ModelInferenceRequestSchema,
    RadecToAltAzRequestSchema,
    ResolvedCatalogIcrsSchema,
    SetTelescopeTrackingRequestSchema,
    TelescopeCapabilitiesSchema,
    TelescopeCommandAckSchema,
    TelescopeMcpContextSchema,
    TelescopeMcpPlanningGuideSchema,
    TelescopeMcpToolManifestSchema,
    TelescopeStatusSchema,
)
from logic.init import init_container
from logic.commands.model_inference import EnqueueModelInferenceCommand
from logic.commands.telescope_control import (
    SetTelescopeTrackingCommand,
    SlewToIcrsCommand,
    SyncMountToIcrsCommand,
)
from logic.mediator.base import Mediator
from logic.queries.catalog import ResolveCommonNameToIcrsQuery
from logic.queries.coordinates import GetHorizontalFromIcrsQuery
from logic.queries.ephemeris import GetSolarSystemBodyIcrsQuery
from logic.queries.command_audit import ListCommandAuditQuery
from logic.queries.model_inference import GetModelInferenceResultQuery
from logic.queries.telescope import GetTelescopeStatusQuery
from settings.config import Config


router = APIRouter(tags=['telescope'])


async def _wait_for_inference_result(
    mediator: Mediator,
    *,
    request_id: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> ModelInferenceResultSchema:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while True:
        result = await mediator.handle_query(GetModelInferenceResultQuery(request_id=request_id))
        if result is not None:
            return ModelInferenceResultSchema(**result)
        if asyncio.get_running_loop().time() >= deadline:
            raise HTTPException(
                status_code=504,
                detail=f'Inference result timeout exceeded for request_id={request_id}; retry with larger timeout_seconds or poll /model/inference/{request_id}',
            )
        await asyncio.sleep(poll_interval_seconds)


@router.get('/tools/mcp-manifest', response_model=TelescopeMcpToolManifestSchema)
async def get_mcp_tool_manifest():
    container = init_container()
    config: Config = container.resolve(Config)
    requires_command_token = bool(config.command_auth_token)

    return TelescopeMcpToolManifestSchema(
        tools=[
            {
                'tool_name': 'telescope.get_status',
                'description': 'Read current telescope status with optional live Alpaca snapshot and capabilities.',
                'method': 'GET',
                'endpoint': '/telescopes/status',
                'requirements': {
                    'required_capability': None,
                    'requires_command_token': False,
                },
            },
            {
                'tool_name': 'telescope.get_context',
                'description': 'Read MCP context aggregate (status/capabilities/catalog/ephemeris warnings).',
                'method': 'GET',
                'endpoint': '/telescopes/context/mcp',
                'requirements': {
                    'required_capability': None,
                    'requires_command_token': False,
                },
            },
            {
                'tool_name': 'telescope.slew_icrs',
                'description': 'Move telescope mount to requested ICRS RA/Dec target.',
                'method': 'POST',
                'endpoint': '/telescopes/commands/slew-icrs',
                'requirements': {
                    'required_capability': 'supports_slew',
                    'requires_command_token': requires_command_token,
                },
            },
            {
                'tool_name': 'telescope.sync_icrs',
                'description': 'Sync telescope mount model to requested ICRS RA/Dec target.',
                'method': 'POST',
                'endpoint': '/telescopes/commands/sync-icrs',
                'requirements': {
                    'required_capability': 'supports_sync',
                    'requires_command_token': requires_command_token,
                },
            },
            {
                'tool_name': 'telescope.set_tracking',
                'description': 'Enable or disable telescope tracking mode.',
                'method': 'POST',
                'endpoint': '/telescopes/commands/tracking',
                'requirements': {
                    'required_capability': 'supports_tracking',
                    'requires_command_token': requires_command_token,
                },
            },
            {
                'tool_name': 'telescope.get_command_audit',
                'description': 'Read command audit trail with optional operation/status/source filters.',
                'method': 'GET',
                'endpoint': '/telescopes/commands/audit',
                'requirements': {
                    'required_capability': None,
                    'requires_command_token': False,
                },
            },
            {
                'tool_name': 'model.enqueue_inference',
                'description': 'Enqueue an inference request for asynchronous model processing.',
                'method': 'POST',
                'endpoint': '/telescopes/model/inference',
                'requirements': {
                    'required_capability': None,
                    'requires_command_token': False,
                },
            },
            {
                'tool_name': 'model.get_inference_status',
                'description': 'Read inference status as pending/completed/failed without 404 while pending.',
                'method': 'GET',
                'endpoint': '/telescopes/model/inference/{request_id}/status',
                'requirements': {
                    'required_capability': None,
                    'requires_command_token': False,
                },
            },
            {
                'tool_name': 'model.wait_inference_result',
                'description': 'Wait for inference completion with timeout and poll interval controls.',
                'method': 'GET',
                'endpoint': '/telescopes/model/inference/{request_id}/wait',
                'requirements': {
                    'required_capability': None,
                    'requires_command_token': False,
                },
            },
            {
                'tool_name': 'model.enqueue_and_wait_inference',
                'description': 'Enqueue an inference request and wait for completion in a single call.',
                'method': 'POST',
                'endpoint': '/telescopes/model/inference/enqueue-and-wait',
                'requirements': {
                    'required_capability': None,
                    'requires_command_token': False,
                },
            },
        ],
    )


@router.get('/tools/mcp-planning-guide', response_model=TelescopeMcpPlanningGuideSchema)
async def get_mcp_planning_guide():
    return TelescopeMcpPlanningGuideSchema(
        objective='Provide a deterministic MCP-safe model inference orchestration guide for local agents.',
        safety_notes=[
            'Prefer read-only status checks before long waits to avoid unnecessary blocking.',
            'Treat pending status as expected for async Kafka workflows; do not retry enqueue immediately.',
            'Use enqueue-and-wait only when synchronous UX is required and timeout budget is known.',
        ],
        inference_flow=[
            {
                'step': 1,
                'tool_name': 'model.enqueue_inference',
                'purpose': 'Submit prompt into async Kafka inference pipeline.',
                'when_to_use': 'Use for non-blocking flows where polling is acceptable.',
            },
            {
                'step': 2,
                'tool_name': 'model.get_inference_status',
                'purpose': 'Check pending/completed/failed state without 404 transitions.',
                'when_to_use': 'Use for periodic progress checks in planners or UIs.',
            },
            {
                'step': 3,
                'tool_name': 'model.wait_inference_result',
                'purpose': 'Block until completion or timeout with bounded polling interval.',
                'when_to_use': 'Use when caller can spend a bounded waiting window.',
            },
            {
                'step': 4,
                'tool_name': 'model.enqueue_and_wait_inference',
                'purpose': 'Combine enqueue and wait in one round-trip for simple clients.',
                'when_to_use': 'Use for single-shot tasks where a synchronous answer is preferred.',
            },
        ],
        timeout_policy={
            'default_timeout_seconds': 15.0,
            'max_timeout_seconds': 60.0,
            'default_poll_interval_seconds': 0.5,
            'max_poll_interval_seconds': 2.0,
        },
    )


def _require_command_auth(x_command_token: str | None):
    container = init_container()
    config: Config = container.resolve(Config)
    expected = config.command_auth_token
    if expected is None:
        return
    if x_command_token != expected:
        raise HTTPException(status_code=401, detail='Missing or invalid command auth token')


@router.get('/status', response_model=TelescopeStatusSchema)
async def get_telescope_status():
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        response = await mediator.handle_query(GetTelescopeStatusQuery())
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc

    return TelescopeStatusSchema(**response)


@router.get('/capabilities', response_model=TelescopeCapabilitiesSchema)
async def get_telescope_capabilities():
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        response = await mediator.handle_query(GetTelescopeStatusQuery())
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc

    return TelescopeCapabilitiesSchema(**response['capabilities'])


@router.get('/context/mcp', response_model=TelescopeMcpContextSchema)
async def get_mcp_context(
    designation: Annotated[str | None, Query(description='Optional catalog object to resolve via Sesame.')] = None,
    ephemeris_body: Annotated[str | None, Query(description='Optional Solar System body (e.g. mars).')] = None,
    obstime_utc_iso: Annotated[str | None, Query(description='UTC instant for ephemeris query, required with ephemeris_body.')] = None,
):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    warnings: list[McpContextWarningSchema] = []
    telescope_status = None
    capabilities = TelescopeCapabilitiesSchema(
        supports_slew=False,
        supports_sync=False,
        supports_tracking=False,
        source='default-disabled',
    )

    try:
        status_payload = await mediator.handle_query(GetTelescopeStatusQuery())
        telescope_status = TelescopeStatusSchema(**status_payload)
        capabilities = TelescopeCapabilitiesSchema(**status_payload['capabilities'])
    except InfrastructureUnavailableException as exc:
        warnings.append(McpContextWarningSchema(source='status', code='infra_unavailable', message=exc.message))

    catalog_target = None
    if designation is not None and designation.strip():
        try:
            catalog_payload = await mediator.handle_query(
                ResolveCommonNameToIcrsQuery(designation=designation.strip()),
            )
            catalog_target = ResolvedCatalogIcrsSchema(**catalog_payload)
        except (CatalogLookupDisabledException, CatalogLookupTimeoutException, UnresolvedObjectNameException) as exc:
            warnings.append(McpContextWarningSchema(source='catalog', code='catalog_unavailable', message=exc.message))

    ephemeris_target = None
    if ephemeris_body is not None and ephemeris_body.strip():
        if not obstime_utc_iso:
            warnings.append(
                McpContextWarningSchema(
                    source='ephemeris',
                    code='missing_obstime',
                    message='obstime_utc_iso is required when ephemeris_body is provided',
                ),
            )
        else:
            try:
                ephemeris_payload = await mediator.handle_query(
                    GetSolarSystemBodyIcrsQuery(
                        body=ephemeris_body.strip(),
                        obstime_utc_iso=obstime_utc_iso,
                    ),
                )
                ephemeris_target = EphemerisIcrsResponseSchema(**ephemeris_payload)
            except (EphemerisDisabledException, EphemerisUnavailableException) as exc:
                warnings.append(McpContextWarningSchema(source='ephemeris', code='ephemeris_unavailable', message=exc.message))

    return TelescopeMcpContextSchema(
        capabilities=capabilities,
        telescope_status=telescope_status,
        catalog_target=catalog_target,
        ephemeris_target=ephemeris_target,
        warnings=warnings,
    )


@router.post('/coordinates/radec-to-altaz', response_model=HorizontalCoordsResponseSchema)
async def radec_to_altaz(schema: RadecToAltAzRequestSchema):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        result = await mediator.handle_query(
            GetHorizontalFromIcrsQuery(
                ra_hours=schema.ra_hours,
                dec_degrees=schema.dec_degrees,
                latitude_deg=schema.latitude_deg,
                longitude_deg=schema.longitude_deg,
                elevation_m=schema.elevation_m,
                obstime_utc_iso=schema.obstime_utc_iso,
            ),
        )
    except CoordinateTransformException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return HorizontalCoordsResponseSchema(**result)


@router.post('/commands/slew-icrs', response_model=TelescopeCommandAckSchema)
async def slew_mount_to_icrs(
    body: IcrsHourAngleDecSchema,
    x_command_token: Annotated[str | None, Header(alias='X-Command-Token')] = None,
):
    _require_command_auth(x_command_token)
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        await mediator.handle_command(
            SlewToIcrsCommand(ra_hours=body.ra_hours, dec_degrees=body.dec_degrees),
        )
    except AlpacaDriverException as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc

    return TelescopeCommandAckSchema()


@router.post('/commands/sync-icrs', response_model=TelescopeCommandAckSchema)
async def sync_mount_to_icrs(
    body: IcrsHourAngleDecSchema,
    x_command_token: Annotated[str | None, Header(alias='X-Command-Token')] = None,
):
    _require_command_auth(x_command_token)
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        await mediator.handle_command(
            SyncMountToIcrsCommand(ra_hours=body.ra_hours, dec_degrees=body.dec_degrees),
        )
    except AlpacaDriverException as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc

    return TelescopeCommandAckSchema()


@router.post('/commands/tracking', response_model=TelescopeCommandAckSchema)
async def set_telescope_tracking(
    body: SetTelescopeTrackingRequestSchema,
    x_command_token: Annotated[str | None, Header(alias='X-Command-Token')] = None,
):
    _require_command_auth(x_command_token)
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        await mediator.handle_command(SetTelescopeTrackingCommand(enabled=body.enabled))
    except AlpacaDriverException as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc

    return TelescopeCommandAckSchema()


@router.get('/commands/audit', response_model=list[CommandAuditRecordSchema])
async def list_command_audits(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    operation: Annotated[str | None, Query(description='Optional operation filter (slew-icrs/sync-icrs/set-tracking).')] = None,
    status: Annotated[str | None, Query(description='Optional status filter (e.g. ok).')] = None,
    source: Annotated[str | None, Query(description='Optional source filter (e.g. main-backend).')] = None,
):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        items = await mediator.handle_query(
            ListCommandAuditQuery(limit=limit, operation=operation, status=status, source=source),
        )
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc

    return [CommandAuditRecordSchema(**item) for item in items]


@router.get('/catalog/icrs', response_model=ResolvedCatalogIcrsSchema)
async def catalog_resolve_icrs(
    designation: Annotated[str, Query(min_length=1, description='Object name Sesame resolves (object catalog).')],
):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        payload = await mediator.handle_query(
            ResolveCommonNameToIcrsQuery(designation=designation.strip()),
        )
    except CatalogLookupDisabledException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc
    except CatalogLookupTimeoutException as exc:
        raise HTTPException(status_code=504, detail=exc.message) from exc
    except UnresolvedObjectNameException as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    return ResolvedCatalogIcrsSchema(**payload)


@router.get('/ephemeris/icrs', response_model=EphemerisIcrsResponseSchema)
async def ephemeris_icrs(
    body: Annotated[str, Query(min_length=1, description='Solar system target name, e.g. mars.')],
    obstime_utc_iso: Annotated[str, Query(description='UTC instant in ISO-8601 format.')],
):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        payload = await mediator.handle_query(
            GetSolarSystemBodyIcrsQuery(
                body=body,
                obstime_utc_iso=obstime_utc_iso,
            ),
        )
    except EphemerisDisabledException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc
    except EphemerisUnavailableException as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return EphemerisIcrsResponseSchema(**payload)


@router.post('/model/inference', response_model=ModelInferenceEnqueuedSchema)
async def enqueue_model_inference(schema: ModelInferenceRequestSchema):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    result = await mediator.handle_command(EnqueueModelInferenceCommand(prompt=schema.prompt))

    return ModelInferenceEnqueuedSchema(**result[0])


@router.post('/model/inference/enqueue-and-wait', response_model=ModelInferenceResultSchema)
async def enqueue_and_wait_model_inference(
    schema: ModelInferenceRequestSchema,
    timeout_seconds: Annotated[float, Query(gt=0, le=60)] = 15.0,
    poll_interval_seconds: Annotated[float, Query(gt=0, le=2)] = 0.5,
):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        result = await mediator.handle_command(EnqueueModelInferenceCommand(prompt=schema.prompt))
        request_id = result[0]['request_id']
        return await _wait_for_inference_result(
            mediator,
            request_id=request_id,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc


@router.get('/model/inference/{request_id}', response_model=ModelInferenceResultSchema)
async def get_model_inference_result(request_id: str):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        result = await mediator.handle_query(GetModelInferenceResultQuery(request_id=request_id))
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc

    if result is None:
        raise HTTPException(status_code=404, detail='Inference result not found')

    return ModelInferenceResultSchema(**result)


@router.get('/model/inference/{request_id}/status', response_model=ModelInferenceStatusSchema)
async def get_model_inference_status(request_id: str):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        result = await mediator.handle_query(GetModelInferenceResultQuery(request_id=request_id))
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc

    if result is None:
        return ModelInferenceStatusSchema(
            request_id=request_id,
            status='pending',
            result=None,
        )

    status = str(result.get('status', '')).strip().lower()
    normalized_status = 'failed' if status == 'failed' else 'completed'
    return ModelInferenceStatusSchema(
        request_id=request_id,
        status=normalized_status,
        result=ModelInferenceResultSchema(**result),
    )


@router.get('/model/inference/{request_id}/wait', response_model=ModelInferenceResultSchema)
async def wait_model_inference_result(
    request_id: str,
    timeout_seconds: Annotated[float, Query(gt=0, le=60)] = 15.0,
    poll_interval_seconds: Annotated[float, Query(gt=0, le=2)] = 0.5,
):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        return await _wait_for_inference_result(
            mediator,
            request_id=request_id,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc
