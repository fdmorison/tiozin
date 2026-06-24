from tiozin.api import State, StateRegistry


class StateRegistryStub(StateRegistry):
    def __init__(self):
        super().__init__(location="stub://state")

    def register(self, state: State) -> State:
        return state

    def latest_cursor(self, state: State) -> State | None:
        return None

    def list_pending(self, state: State) -> list[State]:
        return []

    def begin(self, state: State, attributes: dict = None) -> State:
        return state

    def commit(self, state: State, attributes: dict = None) -> State:
        return state

    def fail(self, state: State, attributes: dict = None) -> State:
        return state

    def cancel(self, state: State, attributes: dict = None) -> State:
        return state

    def quarantine(self, state: State, attributes: dict = None) -> State:
        return state

    def replay(self, state: State, attributes: dict = None) -> State:
        return state
