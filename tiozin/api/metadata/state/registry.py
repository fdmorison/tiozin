from ..registry import Registry
from .model import State


class StateRegistry(Registry[State]):
    """
    Registry for tracking pipeline state.

    Storage-agnostic contract for state backends (databases, key-value stores, etc.).
    Supports both watermark tracking (single record per taxonomy) and pending-events
    tracking (multiple records per taxonomy partition).
    Available in Context for custom inspection in Transforms, Inputs, and Outputs.
    """

    def register(self, state: State) -> State:
        return state

    def latest_cursor(self, state: State) -> State | None:
        return None

    def list_pending(self, state: State) -> list[State]:
        return []

    def start(self, state: State, attributes: dict = None) -> State:
        return state

    def commit(self, state: State, attributes: dict = None) -> State:
        return state

    def rollback(self, state: State, attributes: dict = None) -> State:
        return state

    def cancel(self, state: State, attributes: dict = None) -> State:
        return state

    def quarantine(self, state: State, attributes: dict = None) -> State:
        return state

    def replay(self, state: State, attributes: dict = None) -> State:
        return state
