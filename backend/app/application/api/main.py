from contextlib import asynccontextmanager

from fastapi import FastAPI

from aiojobs import Scheduler
from punq import Container

from application.api.lifespan import (
    close_kafka_broker,
    consume_model_inference_results,
    init_kafka_broker,
)
from application.api.system.handlers import router as system_router
from application.api.telescope.handlers import router as telescope_router
from logic.init import init_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_kafka_broker()

    container: Container = init_container()
    scheduler: Scheduler = container.resolve(Scheduler)
    job = await scheduler.spawn(consume_model_inference_results())

    yield
    await job.close()
    await close_kafka_broker()


def create_app() -> FastAPI:
    app = FastAPI(
        title='Alpaca Astro Center Backend',
        docs_url='/api/docs',
        description='Local-first DDD backend for ASCOM Alpaca telescope control.',
        debug=True,
        lifespan=lifespan,
    )
    app.include_router(system_router)
    app.include_router(telescope_router, prefix='/telescopes')

    return app
