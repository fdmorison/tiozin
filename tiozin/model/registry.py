from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin.model import Component, Plugable
from tiozin.utils import helpers

T = TypeVar("T")


class Registry(Plugable, Component, Generic[T]):
    """
    Base class for metadata registries.

    Stores and retrieves metadata for resources, configurations, or entities.
    Subclasses define storage and retrieval implementation.
    """

    def __init__(self, **kwargs) -> None:
        self.registry_kind = helpers.detect_base_kind(self, Registry)
        self.ready = False
        super().__init__(**kwargs)

    @abstractmethod
    def get(self, identifier: str, failfast: bool = False) -> T:
        """
        Retrieve metadata by identifier.

        Args:
            identifier: Metadata name or unique ID.
            failfast: Raise if not found (default: False).

        Returns:
            Metadata value, or None if not found and failfast=False.

        Raises:
            NotFoundException: When identifier not found and failfast=True.
        """

    @abstractmethod
    def register(self, identifier: str, value: T) -> None:
        """
        Register metadata in the registry.

        Args:
            identifier: Metadata name or unique ID.
            value: Metadata value.
        """
