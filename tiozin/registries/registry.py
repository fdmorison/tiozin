from abc import ABC, abstractmethod
import logging
from typing import Generic, TypeVar

T = TypeVar("T")


class MetadataRegistry(ABC, Generic[T]):
    """
    Base class representing a registry of metadata items.

    A MetadataRegistry manages, stores, and provides access to metadata that
    describes resources, configurations, or system entities. Subclasses must
    define how metadata is stored and retrieved.

    Common use cases include registering schemas, configurations, or catalogs.
    """

    def __init__(self) -> None:
        self.name = type(self).__name__
        self.logger = logging.getLogger(self.name)
        self.ready = False

    def setup(self) -> None:
        """
        Initialize the metadata registry.

        Should prepare any resources required for the registry to function,
        such as connections, caches, or internal data structures.
        """

    def shutdown(self) -> None:
        """
        Gracefully shut down the metadata registry.

        Should release resources, close connections, and ensure consistency
        of the stored metadata.
        """

    @abstractmethod
    def get(self, identifier: str, failfast: bool = False) -> T:
        """
        Retrieve the metadata associated with the given identifier.

        Args:
            identifier: name or unique identifier of the metadata.
            failfast: if True, raise immediately if the identifier is not found.

        Returns:
            The metadata value, otherwise None when failfast is false.

        Raises:
            tiozin.exceptions.NotFoundException: if identifier cannot be found.
        """

    @abstractmethod
    def register(self, identifier: str, value: T) -> None:
        """
        Register a metadata item in the registry.

        Args:
            identifier: name or unique identifier of the metadata.
            value: value of type T associated with the metadata.
        """

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'"{self.name}"'
