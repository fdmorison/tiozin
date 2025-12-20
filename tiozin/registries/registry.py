from abc import ABC, abstractmethod
import logging
from typing import Generic, TypeVar

T = TypeVar("T")


class MetadataRegistry(ABC, Generic[T]):
    """
    Base class for metadata registries.

    Stores and retrieves metadata for resources, configurations, or entities.
    Subclasses define storage and retrieval implementation.
    """

    def __init__(self) -> None:
        self.name = type(self).__name__
        self.logger = logging.getLogger(self.name)
        self.ready = False

    def setup(self) -> None:
        """
        Initialize the registry.

        Prepare connections, caches, or internal structures as needed.
        """

    def shutdown(self) -> None:
        """
        Shut down the registry.

        Release resources and close connections.
        """

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

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'"{self.name}"'
