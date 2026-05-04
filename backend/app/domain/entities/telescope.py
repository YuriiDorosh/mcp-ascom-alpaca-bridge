from dataclasses import dataclass

from domain.entities.base import BaseEntity


@dataclass(eq=False)
class Telescope(BaseEntity):
    name: str = 'Primary Telescope'
    connection_state: str = 'disconnected'
    tracking_enabled: bool = False
