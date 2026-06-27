from collections.abc import Mapping
from typing import Any, TypedDict


class ResourceKwargs(TypedDict):
    """
    Type hints for resource identification keyword arguments.

    Covers the full set of fields that uniquely identify a resource
    across domain, subdomain, layer, product, and model dimensions.
    """

    org: str
    region: str
    domain: str
    subdomain: str
    layer: str
    product: str
    model: str


class LogKwargs(TypedDict, total=False):
    """
    Type hints for logging keyword arguments.

    Provides autocomplete and type safety for standard logging kwargs
    used in Loggable logging methods.
    """

    exc_info: bool | BaseException | tuple[type[BaseException], BaseException, Any] | None
    stack_info: bool | None
    stacklevel: int
    extra: Mapping[str, Any]
