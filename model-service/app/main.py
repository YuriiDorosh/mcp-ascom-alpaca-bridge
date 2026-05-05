from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.kafka_worker import KafkaInferenceWorker
from app.settings import Config

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
        'worker_enabled': config.model_worker_enabled,
    }
