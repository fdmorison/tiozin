from typing import Any, TypedDict


class LogKwargs(TypedDict, total=False):
    """
    Type hints for logging method kwargs.

    Provides autocomplete and type safety for standard logging keyword arguments
    used in Resource logging methods (debug, info, warning, error, critical).
    """

    exc_info: bool | BaseException | tuple[type[BaseException], BaseException, Any] | None
    stack_info: bool
    stacklevel: int
    extra: dict[str, Any]
