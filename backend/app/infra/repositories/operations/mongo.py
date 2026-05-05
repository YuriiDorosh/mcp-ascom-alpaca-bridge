from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import (
    OperationFailure,
    PyMongoError,
    ServerSelectionTimeoutError,
)

from domain.exceptions.infrastructure import InfrastructureUnavailableException
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
        try:
            await self._collection.update_one(
                {'request_id': request_id},
                {'$set': payload},
                upsert=True,
            )
            return payload
        except OperationFailure as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB authorization failed while saving inference result',
            ) from exc
        except ServerSelectionTimeoutError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB server is unreachable while saving inference result',
            ) from exc
        except PyMongoError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB operation failed while saving inference result',
            ) from exc

    async def get_by_request_id(self, request_id: str) -> dict | None:
        try:
            return await self._collection.find_one({'request_id': request_id}, {'_id': 0})
        except OperationFailure as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB authorization failed while reading inference result',
            ) from exc
        except ServerSelectionTimeoutError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB server is unreachable while reading inference result',
            ) from exc
        except PyMongoError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB operation failed while reading inference result',
            ) from exc

    async def save_command_audit(
        self,
        *,
        operation: str,
        status: str,
        details: dict,
        source: str,
    ) -> dict:
        payload = {
            'record_type': 'command_audit',
            'audit_id': str(uuid4()),
            'operation': operation,
            'status': status,
            'details': details,
            'source': source,
            'recorded_at': datetime.now().isoformat(),
        }
        try:
            await self._collection.insert_one(payload)
            return {k: v for k, v in payload.items() if k != '_id'}
        except OperationFailure as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB authorization failed while saving command audit',
            ) from exc
        except ServerSelectionTimeoutError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB server is unreachable while saving command audit',
            ) from exc
        except PyMongoError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB operation failed while saving command audit',
            ) from exc

    async def list_command_audits(
        self,
        *,
        limit: int = 50,
        operation: str | None = None,
        status: str | None = None,
        source: str | None = None,
    ) -> list[dict]:
        try:
            query = {'record_type': 'command_audit'}
            if operation:
                query['operation'] = operation
            if status:
                query['status'] = status
            if source:
                query['source'] = source

            cursor = (
                self._collection.find(query, {'_id': 0})
                .sort('recorded_at', -1)
                .limit(limit)
            )
            return [doc async for doc in cursor]
        except OperationFailure as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB authorization failed while listing command audits',
            ) from exc
        except ServerSelectionTimeoutError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB server is unreachable while listing command audits',
            ) from exc
        except PyMongoError as exc:
            raise InfrastructureUnavailableException(
                details='MongoDB operation failed while listing command audits',
            ) from exc
