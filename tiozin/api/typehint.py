from collections.abc import Mapping
from typing import Any, TypedDict


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
