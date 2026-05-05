from functools import lru_cache

from aiojobs import Scheduler
from aiokafka import (
    AIOKafkaConsumer,
    AIOKafkaProducer,
)
from motor.motor_asyncio import AsyncIOMotorClient
from punq import (
    Container,
    Scope,
)

from infra.message_brokers.base import BaseMessageBroker
from infra.message_brokers.kafka import KafkaMessageBroker
from infra.repositories.operations.base import BaseModelInferenceRepository
from infra.repositories.operations.mongo import MongoDBModelInferenceRepository
from domain.ports.alpaca_client import IAlpacaClient
from domain.ports.coordinate_transform import ICoordinateTransformService
from infra.integrations.alpaca.telescope_client import AlpycaTelescopeClient
from infra.integrations.astropy.coordinate_transform import AstropyCoordinateTransformService
from infra.repositories.telescope.base import BaseTelescopeRepository
from infra.repositories.telescope.mongo import MongoDBTelescopeRepository
from logic.commands.model_inference import (
    EnqueueModelInferenceCommand,
    EnqueueModelInferenceCommandHandler,
)
from logic.mediator.base import Mediator
from logic.mediator.event import EventMediator
from logic.queries.model_inference import (
    GetModelInferenceResultQuery,
    GetModelInferenceResultQueryHandler,
)
from logic.queries.coordinates import (
    GetHorizontalFromIcrsQuery,
    GetHorizontalFromIcrsQueryHandler,
)
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

    def create_mongodb_client():
        return AsyncIOMotorClient(
            config.mongodb_connection_uri,
            serverSelectionTimeoutMS=3000,
        )

    container.register(AsyncIOMotorClient, factory=create_mongodb_client, scope=Scope.singleton)
    mongodb_client = container.resolve(AsyncIOMotorClient)

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

    def create_telescope_repository() -> BaseTelescopeRepository:
        return MongoDBTelescopeRepository(
            mongo_db_client=mongodb_client,
            mongo_db_db_name=config.mongodb_database,
            mongo_db_collection_name=config.mongodb_telescope_collection,
        )

    def create_model_inference_repository() -> BaseModelInferenceRepository:
        return MongoDBModelInferenceRepository(
            mongo_db_client=mongodb_client,
            mongo_db_db_name=config.mongodb_database,
            mongo_db_collection_name=config.mongodb_operation_collection,
        )

    container.register(BaseTelescopeRepository, factory=create_telescope_repository, scope=Scope.singleton)
    container.register(BaseModelInferenceRepository, factory=create_model_inference_repository, scope=Scope.singleton)
    container.register(
        IAlpacaClient,
        factory=lambda: AlpycaTelescopeClient(config=config),
        scope=Scope.singleton,
    )
    container.register(
        ICoordinateTransformService,
        instance=AstropyCoordinateTransformService(),
        scope=Scope.singleton,
    )

    def init_mediator() -> Mediator:
        mediator = Mediator()

        get_telescope_status_handler = GetTelescopeStatusQueryHandler(
            telescope_repository=container.resolve(BaseTelescopeRepository),
            alpaca_client=container.resolve(IAlpacaClient),
        )
        get_horizontal_from_icrs_handler = GetHorizontalFromIcrsQueryHandler(
            transforms=container.resolve(ICoordinateTransformService),
        )
        enqueue_model_inference_handler = EnqueueModelInferenceCommandHandler(
            _mediator=mediator,
            message_broker=container.resolve(BaseMessageBroker),
            config=config,
        )
        get_model_inference_result_handler = GetModelInferenceResultQueryHandler(
            repository=container.resolve(BaseModelInferenceRepository),
        )

        mediator.register_query(
            GetTelescopeStatusQuery,
            get_telescope_status_handler,
        )
        mediator.register_query(
            GetHorizontalFromIcrsQuery,
            get_horizontal_from_icrs_handler,
        )
        mediator.register_query(
            GetModelInferenceResultQuery,
            get_model_inference_result_handler,
        )
        mediator.register_command(
            EnqueueModelInferenceCommand,
            [enqueue_model_inference_handler],
        )

        return mediator

    container.register(Mediator, factory=init_mediator)
    container.register(EventMediator, factory=init_mediator)

    container.register(Scheduler, factory=lambda: Scheduler(), scope=Scope.singleton)

    return container
