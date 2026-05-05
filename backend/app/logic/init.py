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

from domain.ports.alpaca_client import (
    IAlpacaClient,
    IAlpacaTelescopeClient,
)
from domain.ports.catalog_resolve import ICatalogResolveService
from domain.ports.coordinate_transform import ICoordinateTransformService
from domain.ports.ephemeris import IEphemerisService
from infra.integrations.alpaca.telescope_client import AlpycaTelescopeClient
from infra.integrations.astroquery.catalog_resolve import SesameBackedCatalogResolveService
from infra.integrations.astropy.coordinate_transform import AstropyCoordinateTransformService
from infra.integrations.skyfield.ephemeris import SkyfieldEphemerisService
from infra.message_brokers.base import BaseMessageBroker
from infra.message_brokers.kafka import KafkaMessageBroker
from infra.repositories.operations.base import BaseModelInferenceRepository
from infra.repositories.operations.mongo import MongoDBModelInferenceRepository
from infra.repositories.telescope.base import BaseTelescopeRepository
from infra.repositories.telescope.mongo import MongoDBTelescopeRepository
from logic.commands.model_inference import (
    EnqueueModelInferenceCommand,
    EnqueueModelInferenceCommandHandler,
)
from logic.commands.telescope_control import (
    SetTelescopeTrackingCommand,
    SetTelescopeTrackingCommandHandler,
    SlewToIcrsCommand,
    SlewToIcrsCommandHandler,
    SyncMountToIcrsCommand,
    SyncMountToIcrsCommandHandler,
)
from logic.mediator.base import Mediator
from logic.mediator.event import EventMediator
from logic.queries.catalog import (
    ResolveCommonNameToIcrsHandler,
    ResolveCommonNameToIcrsQuery,
)
from logic.queries.command_audit import (
    ListCommandAuditQuery,
    ListCommandAuditQueryHandler,
)
from logic.queries.coordinates import (
    GetHorizontalFromIcrsQuery,
    GetHorizontalFromIcrsQueryHandler,
)
from logic.queries.ephemeris import (
    GetSolarSystemBodyIcrsQuery,
    GetSolarSystemBodyIcrsQueryHandler,
)
from logic.queries.model_inference import (
    GetModelInferenceResultQuery,
    GetModelInferenceResultQueryHandler,
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

    alpaca_telescope_singleton = AlpycaTelescopeClient(config=config)
    container.register(IAlpacaTelescopeClient, instance=alpaca_telescope_singleton, scope=Scope.singleton)
    container.register(IAlpacaClient, instance=alpaca_telescope_singleton, scope=Scope.singleton)

    container.register(
        ICoordinateTransformService,
        instance=AstropyCoordinateTransformService(),
        scope=Scope.singleton,
    )
    container.register(
        ICatalogResolveService,
        factory=lambda: SesameBackedCatalogResolveService(config=config),
        scope=Scope.singleton,
    )
    container.register(
        IEphemerisService,
        factory=lambda: SkyfieldEphemerisService(config=config),
        scope=Scope.singleton,
    )

    def init_mediator() -> Mediator:
        mediator = Mediator()

        alpaca_telescope = container.resolve(IAlpacaTelescopeClient)

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
        list_command_audit_handler = ListCommandAuditQueryHandler(
            repository=container.resolve(BaseModelInferenceRepository),
        )
        slew_to_icrs_handler = SlewToIcrsCommandHandler(
            _mediator=mediator,
            alpaca_telescope=alpaca_telescope,
            message_broker=container.resolve(BaseMessageBroker),
            audit_repository=container.resolve(BaseModelInferenceRepository),
            config=config,
        )
        sync_mount_icrs_handler = SyncMountToIcrsCommandHandler(
            _mediator=mediator,
            alpaca_telescope=alpaca_telescope,
            message_broker=container.resolve(BaseMessageBroker),
            audit_repository=container.resolve(BaseModelInferenceRepository),
            config=config,
        )
        set_tracking_handler = SetTelescopeTrackingCommandHandler(
            _mediator=mediator,
            alpaca_telescope=alpaca_telescope,
            message_broker=container.resolve(BaseMessageBroker),
            audit_repository=container.resolve(BaseModelInferenceRepository),
            config=config,
        )
        resolve_name_handler = ResolveCommonNameToIcrsHandler(
            catalog=container.resolve(ICatalogResolveService),
        )
        get_solar_body_handler = GetSolarSystemBodyIcrsQueryHandler(
            ephemeris=container.resolve(IEphemerisService),
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
        mediator.register_query(
            ListCommandAuditQuery,
            list_command_audit_handler,
        )
        mediator.register_query(
            ResolveCommonNameToIcrsQuery,
            resolve_name_handler,
        )
        mediator.register_query(
            GetSolarSystemBodyIcrsQuery,
            get_solar_body_handler,
        )

        mediator.register_command(
            EnqueueModelInferenceCommand,
            [enqueue_model_inference_handler],
        )
        mediator.register_command(SlewToIcrsCommand, [slew_to_icrs_handler])
        mediator.register_command(SyncMountToIcrsCommand, [sync_mount_icrs_handler])
        mediator.register_command(SetTelescopeTrackingCommand, [set_tracking_handler])

        return mediator

    container.register(Mediator, factory=init_mediator)
    container.register(EventMediator, factory=init_mediator)

    container.register(Scheduler, factory=lambda: Scheduler(), scope=Scope.singleton)

    return container
