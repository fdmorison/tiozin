from abc import abstractmethod
from typing import Generic, TypeVar

from tiozin import config
from tiozin.api import Tiozin
from tiozin.compose import tioproxy
from tiozin.utils import default

from .proxy import RegistryProxy

TMetadata = TypeVar("TMetadata")


@tioproxy(RegistryProxy)
class Registry(Tiozin, Generic[TMetadata]):
    """
    Base class for metadata registries.

    Stores and retrieves metadata for resources, configurations, or entities.
    Subclasses define storage and retrieval implementation.

    Attributes:
        location: Location of the registry backend. Accepts HTTP/HTTPS URLs, FTP URLs,
                  local file paths, or cloud storage URIs (e.g., s3://, gs://, az://).
        readonly: Whether the registry rejects write operations (defaults to False).
        cache: Whether to cache retrieved metadata in memory (defaults to False).
        timeout: Request timeout in seconds.
        ready: Whether the registry has been initialized and is ready to serve requests.
    """

    def __init__(
        self,
        location: str,
        readonly: bool = None,
        cache: bool = None,
        timeout: int = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.location = location
        self.readonly = default(readonly, config.registry_default_readonly)
        self.cache = default(cache, config.registry_default_cache)
        self.timeout = default(timeout, config.registry_default_timeout)
        self.ready = False

    def setup(self, *args, **kwargs) -> None:
        self.ready = True

    def teardown(self, *args, **kwargs) -> None:
        self.ready = False

    @abstractmethod
    def get(self, identifier: str = None, version: str = None) -> TMetadata:
        """
        Retrieve metadata by identifier.

        Raises:
            NotFoundException: When metadata was not found.
        """

    @abstractmethod
    def register(self, identifier: str, value: TMetadata) -> None:
        """Register metadata in the registry."""

    def try_get(self, identifier: str, version: str | None = None) -> TMetadata | None:
        """Retrieve metadata or return None if not found."""
        try:
            return self.get(identifier, version)
        except Exception as e:
            self.warning(str(e))
            return None
