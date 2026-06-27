from typing_extensions import Unpack

from tiozin.api import State, StateRegistry
from tiozin.api.typehint import ResourceKwargs


class NoOpStateRegistry(StateRegistry):
    """
    No-op state registry.

    Does nothing. Returns the received state for all transitions, None for the
    watermark, and an empty list for the backlog.
    Useful for testing or when state tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def register(self, state: State) -> State:
        return state

    def begin(self, state: State) -> State:
        state.status = state.status.to_running()
        return state

    def commit(self, state: State) -> State:
        state.status = state.status.to_succeeded()
        return state

    def fail(self, state: State) -> State:
        state.status = state.status.to_failed()
        return state

    def cancel(self, state: State) -> State:
        state.status = state.status.to_canceled()
        return state

    def quarantine(self, state: State) -> State:
        state.status = state.status.to_quarantined()
        return state

    def replay(self, state: State) -> State:
        state.status = state.status.to_pending()
        return state

    def get_watermark(self, **resource: Unpack[ResourceKwargs]) -> State | None:
        return None

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[State]:
        return []
