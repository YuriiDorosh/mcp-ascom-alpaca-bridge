from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from settings.config import Config


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

    config = Config()
    cors_raw = config.cors_allowed_origins
    if cors_raw is None:
        cors_raw = 'http://localhost:5173,http://127.0.0.1:5173'
    origin_list = [part.strip() for part in cors_raw.split(',') if part.strip()]
    if origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origin_list,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    app.include_router(system_router)
    app.include_router(telescope_router, prefix='/telescopes')

    return app
