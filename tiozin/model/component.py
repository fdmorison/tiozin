from abc import ABC
import logging
from typing import Any, Optional, Self, Unpack

from uuid_utils import uuid7

from .typehint import LogKwargs


class Component(ABC):
    """
    Base class for all Tiozin components.

    Represents a named and identifiable unit within the system. Components
    provide logging, lifecycle hooks, and a unique execution identity, and
    serve as the foundation for higher-level abstractions such as Registries
    and Resources.

    Attributes:
        id: Unique execution identifier for this component instance. Ensures
            each instantiation can be tracked and distinguished, even when
            components share the same name or configuration.
        kind: The component's Python type. Used for runtime type inspection,
            plugin discovery, and determining component behavior without
            relying on string comparisons.
        name: Human-readable identifier for logging and debugging. Defaults
            to the class name if not provided, making components immediately
            identifiable in logs and error messages.
        description: Optional human-readable explanation of the component's
            purpose. Intended for documentation, API responses, and helping
            developers understand what this component does.
        options: Extra keyword arguments not consumed by the component or its
            parent classes in the MRO chain. Allows passing provider-specific
            configurations (e.g., Spark reader/writer options) without polluting
            the component's primary interface.
        logger: Pre-configured logger instance scoped to this component's name.
            Provides consistent logging across the framework without requiring
            manual logger setup in subclasses.
    """

    def __init__(
        self,
        name: str = None,
        description: Optional[str] = None,
        **options,
    ) -> None:
        self.id = str(uuid7())
        self.kind = type(self)
        self.name = name or type(self).__name__
        self.description = description
        self.options = options
        self.logger = logging.getLogger(self.name)

    def setup(self, **kwargs) -> None:
        """
        Optional initialization hook.

        Called when the component enters its execution context.
        Override if the component requires setup logic.
        """

    def teardown(self, **kwargs) -> None:
        """
        Optional cleanup hook.

        Called when the component exits its execution context.
        Override if the component requires cleanup logic.
        """

    def to_dict(self) -> dict[str, Any]:
        """
        Returns a shallow dictionary representation of the component state.
        """
        return vars(self).copy()

    def debug(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs: Unpack[LogKwargs]) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def __enter__(self) -> Self:
        """
        Enters the component execution context and triggers setup.
        """
        self.setup()
        return self

    def __exit__(self, clazz, error, trace) -> None:
        """
        Exits the component execution context and triggers teardown.
        """
        self.teardown()

    def __str__(self) -> str:
        """Returns a simple string representation of the component."""
        return self.name

    def __repr__(self) -> str:
        """Returns a concise string representation of the component."""
        return f'"{self.name}"'

    def __hash__(self) -> int:
        """
        Hashes the component using its unique execution identifier.
        """
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """
        Compares components by execution identity.
        """
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
