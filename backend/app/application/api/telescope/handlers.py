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
    ModelInferenceRequestSchema,
    RadecToAltAzRequestSchema,
    ResolvedCatalogIcrsSchema,
    SetTelescopeTrackingRequestSchema,
    TelescopeCapabilitiesSchema,
    TelescopeCommandAckSchema,
    TelescopeMcpContextSchema,
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
async def list_command_audits(limit: Annotated[int, Query(ge=1, le=200)] = 50):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        items = await mediator.handle_query(ListCommandAuditQuery(limit=limit))
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
