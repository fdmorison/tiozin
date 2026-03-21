from __future__ import annotations

from collections.abc import Collection
from typing import Any, Self

from tiozin.exceptions.base import TiozinUsageError


class TiozinNotFoundError(TiozinUsageError):
    """
    Raised when a requested resource cannot be found.
    """

    http_status = 404
    message = "The requested resource could not be found."


class TiozinConflictError(TiozinUsageError):
    """
    Raised when an operation conflicts with the current state of a resource.
    """

    http_status = 409
    message = "The operation conflicts with the current state of the resource."


class TiozinTimeoutError(TiozinUsageError):
    """
    Raised when an operation exceeds its time limit.
    """

    http_status = 408
    retryable = True
    message = "The operation exceeded the time limit and timed out."


class TiozinForbiddenError(TiozinUsageError):
    """
    Raised when access to a resource or operation is forbidden.
    """

    http_status = 403
    message = "You are not allowed to perform this operation."


class TiozinInputError(TiozinUsageError):
    """
    Raised when input fails validation rules.
    """

    http_status = 422
    message = "The input failed validation. Please review and correct the errors."

    @classmethod
    def raise_if_not_in(
        cls,
        value: Any,
        options: Collection,
        message: str = None,
        allow_none: bool = False,
    ) -> type[Self]:
        """
        Guard-style helper that raises this exception if ``value`` is not in ``options``.

        When ``allow_none`` is ``True``, a ``None`` value is always accepted regardless
        of whether ``None`` appears in ``options``.
        """
        if allow_none and value is None:
            return cls
        if value not in options:
            opts = ", ".join(str(o) for o in sorted(options))
            raise cls(message or f"Invalid value '{value}'. Must be one of: {opts}")
        return cls


class TiozinPreconditionError(TiozinUsageError):
    """
    Raised when a required precondition for the operation is not satisfied.

    The request is valid and the input is correct, but the system is not
    in the right state to proceed. Common in ETL pipelines where operations
    depend on upstream jobs, registered schemas, or prepared environments.

    Distinct from ``TiozinConflictError``, which signals a conflict with
    the state of the target resource itself.
    """

    http_status = 412
    message = "A required precondition for this operation was not met."


class TiozinUnavailableError(TiozinUsageError):
    """
    Raised when an external dependency is temporarily unavailable.

    Indicates that a required service, registry, or data source cannot be
    reached at this time. Common in ETL pipelines that depend on external
    systems such as databases, storage backends, or remote APIs.

    This error is transient and the operation may succeed on retry.
    """

    http_status = 503
    retryable = True
    message = "A required service or resource is temporarily unavailable."


class TiozinNotImplementedError(TiozinUsageError):
    """
    Raised when a requested capability is not implemented by the plugin.

    Indicates that the Tiozin does not support the invoked operation for
    its current configuration or role. Distinct from Python's built-in
    ``NotImplementedError``, this integrates with the Tiozin error hierarchy
    and can be caught alongside other usage errors.
    """

    http_status = 501
    message = "This operation is not implemented by the current plugin."
