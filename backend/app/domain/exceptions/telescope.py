from dataclasses import dataclass

from domain.exceptions.base import ApplicationException


@dataclass(eq=False)
class AlpacaDriverException(ApplicationException):
    reason: str

    @property
    def message(self) -> str:
        return self.reason


@dataclass(eq=False)
class CoordinateTransformException(ApplicationException):
    reason: str

    @property
    def message(self) -> str:
        return self.reason


@dataclass(eq=False)
class EphemerisUnavailableException(ApplicationException):
    reason: str

    @property
    def message(self) -> str:
        return self.reason
