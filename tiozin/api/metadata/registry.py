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

    Handles storage and retrieval of metadata.
    Subclasses define how data is persisted and accessed.

    Attributes:
        location: Registry backend location (e.g., HTTP/HTTPS, FTP, local path, s3://, gs://, az://)
        readonly: If True, disables write operations
        cache: If True, enables in-memory caching
        timeout: Request timeout in seconds
        failfast: If True, raises an error when metadata is not found; if False, returns None
        ready: Indicates if the registry is initialized and ready
    """

    def __init__(
        self,
        location: str,
        readonly: bool = None,
        cache: bool = None,
        timeout: int = None,
        failfast: bool = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.location = location
        self.readonly = default(readonly, config.registry_default_readonly)
        self.cache = default(cache, config.registry_default_cache)
        self.timeout = default(timeout, config.registry_default_timeout)
        self.failfast = default(failfast, config.registry_default_failfast)
        self.ready = False

    def setup(self, *args, **kwargs) -> None:
        self.ready = True

    def teardown(self, *args, **kwargs) -> None:
        self.ready = False
