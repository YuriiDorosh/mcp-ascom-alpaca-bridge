from dataclasses import dataclass

from domain.events.telescope import (
    TelescopeConnectionStateChangedEvent,
    TelescopeTrackingChangedEvent,
)
from domain.entities.base import BaseEntity


@dataclass(eq=False)
class Telescope(BaseEntity):
    name: str = 'Primary Telescope'
    connection_state: str = 'disconnected'
    tracking_enabled: bool = False

    def set_connection_state(self, new_state: str) -> None:
        if self.connection_state == new_state:
            return

        previous_state = self.connection_state
        self.connection_state = new_state
        self.register_event(
            TelescopeConnectionStateChangedEvent(
                telescope_oid=self.oid,
                previous_state=previous_state,
                new_state=new_state,
            ),
        )

    def set_tracking_enabled(self, enabled: bool) -> None:
        if self.tracking_enabled == enabled:
            return

        previous_tracking_enabled = self.tracking_enabled
        self.tracking_enabled = enabled
        self.register_event(
            TelescopeTrackingChangedEvent(
                telescope_oid=self.oid,
                previous_tracking_enabled=previous_tracking_enabled,
                new_tracking_enabled=enabled,
            ),
        )
