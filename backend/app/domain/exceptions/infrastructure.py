from dataclasses import dataclass

from domain.exceptions.base import ApplicationException


@dataclass(eq=False)
class InfrastructureUnavailableException(ApplicationException):
    details: str

    @property
    def message(self):
        return f'Infrastructure dependency is unavailable: {self.details}'
