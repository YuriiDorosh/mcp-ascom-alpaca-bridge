from fastapi import APIRouter


router = APIRouter(tags=['system'])


@router.get('/health')
async def healthcheck():
    return {'status': 'ok'}


@router.get('/ready')
async def readiness():
    return {'status': 'ready'}
