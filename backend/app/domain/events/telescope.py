from dataclasses import dataclass
from typing import ClassVar

from domain.events.base import BaseEvent


@dataclass
class TelescopeConnectionStateChangedEvent(BaseEvent):
    event_title: ClassVar[str] = 'telescope.connection_state_changed'

    telescope_oid: str
    previous_state: str
    new_state: str


@dataclass
class TelescopeTrackingChangedEvent(BaseEvent):
    event_title: ClassVar[str] = 'telescope.tracking_changed'

    telescope_oid: str
    previous_tracking_enabled: bool
    new_tracking_enabled: bool
