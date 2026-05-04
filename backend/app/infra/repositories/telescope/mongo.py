from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient

from domain.entities.telescope import Telescope
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
        record = await self._collection.find_one(sort=[('created_at', 1)])
        if record:
            return convert_mongo_doc_to_telescope(record)

        telescope = Telescope()
        await self.save_primary(telescope)
        return telescope

    async def save_primary(self, telescope: Telescope) -> Telescope:
        await self._collection.update_one(
            {'oid': telescope.oid},
            {'$set': convert_telescope_to_mongo_doc(telescope)},
            upsert=True,
        )
        return telescope
