from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import (
    OperationFailure,
    PyMongoError,
    ServerSelectionTimeoutError,
)

from domain.entities.telescope import Telescope
from domain.exceptions.infrastructure import InfrastructureUnavailableException
from infra.repositories.telescope.base import BaseTelescopeRepository
from infra.repositories.telescope.converters import (
    convert_mongo_doc_to_telescope,
    convert_telescope_to_mongo_doc,
)


@dataclass
class MongoDBTelescopeRepository(BaseTelescopeRepository):
    mongo_db_client: AsyncIOMotorClient
    mongo_db_db_name: str
    mongo_db_collection_name: str

    @property
    def _collection(self):
        return self.mongo_db_client[self.mongo_db_db_name][self.mongo_db_collection_name]

    async def get_primary(self) -> Telescope:
        try:
            record = await self._collection.find_one(sort=[('created_at', 1)])
            if record:
                return convert_mongo_doc_to_telescope(record)

            telescope = Telescope()
            await self.save_primary(telescope)
            return telescope
        except OperationFailure as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB authorization failed for telescope repository',
            ) from exc
        except ServerSelectionTimeoutError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB server is unreachable for telescope repository',
            ) from exc
        except PyMongoError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB operation failed for telescope repository',
            ) from exc

    async def save_primary(self, telescope: Telescope) -> Telescope:
        try:
            await self._collection.update_one(
                {'oid': telescope.oid},
                {'$set': convert_telescope_to_mongo_doc(telescope)},
                upsert=True,
            )
            return telescope
        except OperationFailure as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB authorization failed while saving telescope state',
            ) from exc
        except ServerSelectionTimeoutError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB server is unreachable while saving telescope state',
            ) from exc
        except PyMongoError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB operation failed while saving telescope state',
            ) from exc
