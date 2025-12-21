from typing import Any

from ...model.registry import Registry


class PluginRegistry(Registry):

    def __init__(self) -> None:
        super().__init__()

    def get(self, name: str) -> None:
        pass

    def register(self, name: str, value: Any) -> None:
        pass
