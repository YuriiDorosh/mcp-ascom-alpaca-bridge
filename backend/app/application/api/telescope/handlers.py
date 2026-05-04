from fastapi import APIRouter
from fastapi import HTTPException

from application.api.telescope.schemas import (
    ModelInferenceEnqueuedSchema,
    ModelInferenceResultSchema,
    ModelInferenceRequestSchema,
    TelescopeStatusSchema,
)
from logic.init import init_container
from logic.commands.model_inference import EnqueueModelInferenceCommand
from logic.mediator.base import Mediator
from logic.queries.model_inference import GetModelInferenceResultQuery
from logic.queries.telescope import GetTelescopeStatusQuery


router = APIRouter(tags=['telescope'])


@router.get('/status', response_model=TelescopeStatusSchema)
async def get_telescope_status():
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    response = await mediator.handle_query(GetTelescopeStatusQuery())

    return TelescopeStatusSchema(**response)


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
    result = await mediator.handle_query(GetModelInferenceResultQuery(request_id=request_id))

    if result is None:
        raise HTTPException(status_code=404, detail='Inference result not found')

    return ModelInferenceResultSchema(**result)
