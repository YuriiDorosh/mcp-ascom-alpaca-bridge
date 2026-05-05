from typing import Annotated

from fastapi import APIRouter
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
    EphemerisIcrsResponseSchema,
    HorizontalCoordsResponseSchema,
    IcrsHourAngleDecSchema,
    ModelInferenceEnqueuedSchema,
    ModelInferenceResultSchema,
    ModelInferenceRequestSchema,
    RadecToAltAzRequestSchema,
    ResolvedCatalogIcrsSchema,
    SetTelescopeTrackingRequestSchema,
    TelescopeCommandAckSchema,
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
from logic.queries.model_inference import GetModelInferenceResultQuery
from logic.queries.telescope import GetTelescopeStatusQuery


router = APIRouter(tags=['telescope'])


@router.get('/status', response_model=TelescopeStatusSchema)
async def get_telescope_status():
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        response = await mediator.handle_query(GetTelescopeStatusQuery())
    except InfrastructureUnavailableException as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc

    return TelescopeStatusSchema(**response)


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
async def slew_mount_to_icrs(body: IcrsHourAngleDecSchema):
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
async def sync_mount_to_icrs(body: IcrsHourAngleDecSchema):
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
async def set_telescope_tracking(body: SetTelescopeTrackingRequestSchema):
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    try:
        await mediator.handle_command(SetTelescopeTrackingCommand(enabled=body.enabled))
    except AlpacaDriverException as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc

    return TelescopeCommandAckSchema()


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
