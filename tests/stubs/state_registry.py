from typing_extensions import Unpack

from tiozin.api import State, StateRegistry
from tiozin.api.typehint import ResourceKwargs


class StateRegistryStub(StateRegistry):
    def __init__(self):
        super().__init__(location="stub://state")

    def register(self, state: State) -> State:
        return state

    def begin(self, state: State) -> State:
        return state

    def commit(self, state: State) -> State:
        return state

    def fail(self, state: State) -> State:
        return state

    def cancel(self, state: State) -> State:
        return state

    def quarantine(self, state: State) -> State:
        return state

    def replay(self, state: State) -> State:
        return state

    def get_watermark(self, **resource: Unpack[ResourceKwargs]) -> State | None:
        return None

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[State]:
        return []
