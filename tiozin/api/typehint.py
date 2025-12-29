from typing import Any, TypedDict


class OperatorKwargs(TypedDict, total=False):
    """
    Type hints for Operator initialization kwargs.

    Provides autocomplete and type safety for Data Mesh metadata attributes
    used when initializing Operator-based classes (Jobs, Inputs, Outputs,
    Transforms, and Runners). These attributes enable discovery, governance,
    and lineage tracking across domains.
    """

    name: str
    description: str
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str


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
