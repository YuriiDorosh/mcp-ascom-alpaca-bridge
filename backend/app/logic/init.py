from functools import lru_cache

from aiojobs import Scheduler
from aiokafka import (
    AIOKafkaConsumer,
    AIOKafkaProducer,
)
from punq import (
    Container,
    Scope,
)

from domain.entities.telescope import Telescope
from infra.message_brokers.base import BaseMessageBroker
from infra.message_brokers.kafka import KafkaMessageBroker
from infra.repositories.telescope.base import BaseTelescopeRepository
from infra.repositories.telescope.memory import InMemoryTelescopeRepository
from logic.mediator.base import Mediator
from logic.mediator.event import EventMediator
from logic.queries.telescope import (
    GetTelescopeStatusQuery,
    GetTelescopeStatusQueryHandler,
)
from settings.config import Config


@lru_cache(1)
def init_container() -> Container:
    return _init_container()


def _init_container() -> Container:
    container = Container()

    container.register(Config, instance=Config(), scope=Scope.singleton)
    config: Config = container.resolve(Config)

    def create_message_broker() -> BaseMessageBroker:
        return KafkaMessageBroker(
            producer=AIOKafkaProducer(bootstrap_servers=config.kafka_url),
            consumer=AIOKafkaConsumer(
                bootstrap_servers=config.kafka_url,
                group_id='alpaca-astro-center',
                metadata_max_age_ms=30000,
            ),
        )

    # Infrastructure
    container.register(BaseMessageBroker, factory=create_message_broker, scope=Scope.singleton)
    container.register(
        BaseTelescopeRepository,
        instance=InMemoryTelescopeRepository(telescope=Telescope()),
        scope=Scope.singleton,
    )

    def init_mediator() -> Mediator:
        mediator = Mediator()

        get_telescope_status_handler = GetTelescopeStatusQueryHandler(
            telescope_repository=container.resolve(BaseTelescopeRepository),
        )

        mediator.register_query(
            GetTelescopeStatusQuery,
            get_telescope_status_handler,
        )

        return mediator

    container.register(Mediator, factory=init_mediator)
    container.register(EventMediator, factory=init_mediator)

    container.register(Scheduler, factory=lambda: Scheduler(), scope=Scope.singleton)

    return container
