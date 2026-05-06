from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.kafka_worker import KafkaInferenceWorker
from app.settings import (
    Config,
    SUPPORTED_RUNTIME_PROFILES,
)

config = Config()
worker = KafkaInferenceWorker(config)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await worker.start()
    try:
        yield
    finally:
        await worker.stop()


app = FastAPI(title='Alpaca Astro Center Model Service', lifespan=lifespan)


@app.get('/health')
async def health():
    return {
        'status': 'ok',
        'runtime_profile': config.model_runtime_profile,
        'supported_runtime_profiles': list(SUPPORTED_RUNTIME_PROFILES),
        'worker_enabled': config.model_worker_enabled,
    }


@app.get('/runtime/profiles')
async def runtime_profiles():
    return {
        'active_profile': config.model_runtime_profile,
        'supported_profiles': list(SUPPORTED_RUNTIME_PROFILES),
    }
