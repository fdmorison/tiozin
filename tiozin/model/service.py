from abc import ABC
import logging
from typing import Any

from uuid_utils import uuid7


class Service(ABC):
    """
    Base class for infrastructure services.

    Services represent system components like apps and registries.
    Each service instance is uniquely identified by a run_id.

    Attributes:
        kind: Service class name.
        name: Service name (equals kind).
        run_id: Unique execution identifier (UUID7).
        logger: Logger scoped to service name.

    Example:
        class MyService(Service):
            pass

        service = MyService()
        service.logger.info("Service started")
    """

    def __init__(self) -> None:
        self.kind = type(self).__name__
        self.name = self.kind
        self.run_id = str(uuid7())
        self.logger = logging.getLogger(self.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'"{self.name}"'

    def __hash__(self) -> int:
        return hash(self.run_id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.run_id == other.run_id
