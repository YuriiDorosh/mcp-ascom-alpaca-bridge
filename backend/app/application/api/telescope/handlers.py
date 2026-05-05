from fastapi import APIRouter
from fastapi import HTTPException

from domain.exceptions.infrastructure import InfrastructureUnavailableException
from domain.exceptions.telescope import CoordinateTransformException
from application.api.telescope.schemas import (
    HorizontalCoordsResponseSchema,
    ModelInferenceEnqueuedSchema,
    ModelInferenceResultSchema,
    ModelInferenceRequestSchema,
    RadecToAltAzRequestSchema,
    TelescopeStatusSchema,
)
from logic.init import init_container
from logic.commands.model_inference import EnqueueModelInferenceCommand
from logic.mediator.base import Mediator
from logic.queries.coordinates import GetHorizontalFromIcrsQuery
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
