from abc import ABC
import logging
from typing import Any, Optional

from uuid_utils import uuid7


class Component(ABC):
    """
    Base class for all Tiozin components.

    Components are identifiable, trackable units in the system with logging capabilities.
    Each component instance is uniquely identified by a run_id and has associated metadata.

    Attributes:
        kind: Component class name.
        name: Component name.
        run_id: Unique execution identifier (UUID7).
        logger: Logger scoped to component name.
        description: Optional human-readable description.

    Example:
        class MyComponent(Component):
            def __init__(self, name: str) -> None:
                super().__init__(name)

        component = MyComponent("my_component")
        component.info("Component created")
        component.warning("This is a warning")
        component.error("Something went wrong")
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> None:
        self.run_id = str(uuid7())
        self.kind = type(self).__name__
        self.name = name
        self.description = description
        self.logger = logging.getLogger(self.name)

    def to_dict(self) -> dict[str, Any]:
        return vars(self).copy()

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)

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
