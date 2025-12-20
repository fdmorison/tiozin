from typing import Any

from ..registry import MetadataRegistry


class PluginRegistry(MetadataRegistry):

    def __init__(self) -> None:
        super().__init__()

    def get(self, name: str) -> None:
        pass

    def register(self, name: str, value: Any) -> None:
        pass
