from abc import ABC
import logging


class Resource(ABC):

    def __init__(self, name: str = None, description: str = None) -> None:
        self.kind = type(self).__name__
        self.name = name or self.kind
        self.description = description
        self.logger = logging.getLogger(self.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'"{self.name}"'
