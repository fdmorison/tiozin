from tiozin.api import StateRegistry


class StateRegistryStub(StateRegistry):
    def __init__(self):
        super().__init__(location="stub://state")

    def get(self, identifier: str = None, version: str = None) -> None:
        return None

    def register(self, identifier: str, value: object) -> None:
        pass
