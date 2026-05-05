import asyncio
from dataclasses import asdict

import orjson
from aiokafka import AIOKafkaConsumer
from aiokafka.producer import AIOKafkaProducer

from app.contracts import (
    ModelInferenceRequestContract,
    ModelInferenceResultContract,
)
from app.runtime import run_inference
from app.settings import Config


class KafkaInferenceWorker:
    def __init__(self, config: Config):
        self._config = config
        self._producer = AIOKafkaProducer(bootstrap_servers=config.kafka_url)
        self._consumer = AIOKafkaConsumer(
            config.model_inference_request_topic,
            bootstrap_servers=config.kafka_url,
            enable_auto_commit=True,
            auto_offset_reset='earliest',
        )
        self._task: asyncio.Task | None = None
        self._running = False
        self._started = False

    async def start(self):
        if not self._config.model_worker_enabled:
            return
        await self._producer.start()
        await self._consumer.start()
        self._running = True
        self._started = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if not self._started:
            return
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._consumer.stop()
        await self._producer.stop()
        self._started = False

    async def _loop(self):
        async for message in self._consumer:
            if not self._running:
                break
            payload = orjson.loads(message.value)
            request = ModelInferenceRequestContract(
                schema_version=payload.get('schema_version', 'v1'),
                request_id=payload['request_id'],
                correlation_id=payload.get('correlation_id', payload['request_id']),
                prompt=payload['prompt'],
                created_at=payload['created_at'],
                source=payload.get('source', 'main-backend'),
            )

            output_text = run_inference(request.prompt, self._config)
            result = ModelInferenceResultContract.completed(
                request_id=request.request_id,
                correlation_id=request.correlation_id,
                output_text=output_text,
                source=self._config.model_service_source,
            )
            await self._producer.send(
                topic=self._config.model_inference_result_topic,
                key=result.request_id.encode(),
                value=orjson.dumps(asdict(result)),
            )
