from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient

from infra.repositories.operations.base import BaseModelInferenceRepository


@dataclass
class MongoDBModelInferenceRepository(BaseModelInferenceRepository):
    mongo_db_client: AsyncIOMotorClient
    mongo_db_db_name: str
    mongo_db_collection_name: str

    @property
    def _collection(self):
        return self.mongo_db_client[self.mongo_db_db_name][self.mongo_db_collection_name]

    async def save_result(
        self,
        request_id: str,
        status: str,
        output_text: str | None,
        error_message: str | None,
        finished_at: str,
    ) -> dict:
        payload = {
            'request_id': request_id,
            'status': status,
            'output_text': output_text,
            'error_message': error_message,
            'finished_at': finished_at,
        }
        await self._collection.update_one(
            {'request_id': request_id},
            {'$set': payload},
            upsert=True,
        )
        return payload

    async def get_by_request_id(self, request_id: str) -> dict | None:
        return await self._collection.find_one({'request_id': request_id}, {'_id': 0})
