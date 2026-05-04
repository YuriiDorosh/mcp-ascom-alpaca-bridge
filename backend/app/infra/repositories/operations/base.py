from abc import (
    ABC,
    abstractmethod,
)


class BaseModelInferenceRepository(ABC):
    @abstractmethod
    async def save_result(
        self,
        request_id: str,
        status: str,
        output_text: str | None,
        error_message: str | None,
        finished_at: str,
    ) -> dict:
        ...

    @abstractmethod
    async def get_by_request_id(self, request_id: str) -> dict | None:
        ...
