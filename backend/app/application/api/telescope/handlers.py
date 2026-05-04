from fastapi import APIRouter

from application.api.telescope.schemas import TelescopeStatusSchema
from logic.init import init_container
from logic.mediator.base import Mediator
from logic.queries.telescope import GetTelescopeStatusQuery


router = APIRouter(tags=['telescope'])


@router.get('/status', response_model=TelescopeStatusSchema)
async def get_telescope_status():
    container = init_container()
    mediator: Mediator = container.resolve(Mediator)
    response = await mediator.handle_query(GetTelescopeStatusQuery())

    return TelescopeStatusSchema(**response)
