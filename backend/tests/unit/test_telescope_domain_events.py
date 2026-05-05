from domain.entities.telescope import Telescope
from domain.events.telescope import (
    TelescopeConnectionStateChangedEvent,
    TelescopeTrackingChangedEvent,
)


def test_telescope_lifecycle_events_are_registered_on_state_change():
    telescope = Telescope()

    telescope.set_connection_state('connected')
    telescope.set_tracking_enabled(True)
    events = telescope.pull_events()

    assert len(events) == 2
    assert isinstance(events[0], TelescopeConnectionStateChangedEvent)
    assert events[0].previous_state == 'disconnected'
    assert events[0].new_state == 'connected'
    assert isinstance(events[1], TelescopeTrackingChangedEvent)
    assert events[1].previous_tracking_enabled is False
    assert events[1].new_tracking_enabled is True


def test_telescope_lifecycle_events_not_registered_for_noop_transitions():
    telescope = Telescope()

    telescope.set_connection_state('disconnected')
    telescope.set_tracking_enabled(False)

    assert telescope.pull_events() == []
