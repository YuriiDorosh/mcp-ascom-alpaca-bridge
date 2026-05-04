from dataclasses import (
    asdict,
    dataclass,
)

import orjson

from infra.message_brokers.base import BaseMessageBroker
from infra.message_brokers.contracts import ModelInferenceRequestContract
from logic.commands.base import (
    BaseCommand,
    CommandHandler,
)
from settings.config import Config


@dataclass(frozen=True)
class EnqueueModelInferenceCommand(BaseCommand):
    prompt: str


@dataclass(frozen=True)
class EnqueueModelInferenceCommandHandler(CommandHandler[EnqueueModelInferenceCommand, dict]):
    message_broker: BaseMessageBroker
    config: Config

    async def handle(self, command: EnqueueModelInferenceCommand) -> dict:
        contract = ModelInferenceRequestContract.create(prompt=command.prompt)
        payload = orjson.dumps(asdict(contract))

        await self.message_broker.send_message(
            key=contract.request_id.encode(),
            topic=self.config.model_inference_request_topic,
            value=payload,
        )

        return {
            'request_id': contract.request_id,
            'topic': self.config.model_inference_request_topic,
        }
