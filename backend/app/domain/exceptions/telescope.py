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


@dataclass(eq=False)
class UnresolvedObjectNameException(ApplicationException):
    object_name: str

    @property
    def message(self) -> str:
        return f'Could not resolve object name "{self.object_name}"'


@dataclass(eq=False)
class CatalogLookupDisabledException(ApplicationException):

    @property
    def message(self) -> str:
        return 'Object name lookups are disabled; set CATALOG_LOOKUP_ENABLED=true in the environment.'


@dataclass(eq=False)
class CatalogLookupTimeoutException(ApplicationException):

    @property
    def message(self) -> str:
        return 'Object name resolution timed out (check CATALOG_RESOLVE_TIMEOUT_SECONDS and network)'
