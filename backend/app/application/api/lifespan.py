from infra.message_brokers.contracts import ModelInferenceResultContract
from infra.message_brokers.base import BaseMessageBroker
from infra.repositories.operations.base import BaseModelInferenceRepository
from logic.init import init_container
from settings.config import Config


async def init_kafka_broker():
    container = init_container()
    message_broker: BaseMessageBroker = container.resolve(BaseMessageBroker)
    await message_broker.start()


async def consume_model_inference_results():
    container = init_container()
    config: Config = container.resolve(Config)
    message_broker: BaseMessageBroker = container.resolve(BaseMessageBroker)
    repository: BaseModelInferenceRepository = container.resolve(BaseModelInferenceRepository)

    async for payload in message_broker.start_consuming(config.model_inference_result_topic):
        result = ModelInferenceResultContract(
            request_id=payload['request_id'],
            status=payload['status'],
            output_text=payload.get('output_text'),
            error_message=payload.get('error_message'),
            finished_at=payload['finished_at'],
        )
        await repository.save_result(
            request_id=result.request_id,
            status=result.status,
            output_text=result.output_text,
            error_message=result.error_message,
            finished_at=result.finished_at,
        )


async def close_kafka_broker():
    container = init_container()
    message_broker: BaseMessageBroker = container.resolve(BaseMessageBroker)
    await message_broker.close()
