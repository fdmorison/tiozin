from tiozin.api import State, StateRegistry


class NoOpStateRegistry(StateRegistry):
    """
    No-op state registry.

    Does nothing. Returns the received state for all transitions, None for the
    latest cursor lookup, and an empty list for pending states.
    Useful for testing or when state tracking is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

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
