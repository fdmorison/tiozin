from __future__ import annotations

from typing import Any, Self


class TiozinError(Exception):
    """
    Base exception for all Tiozin framework errors.

    Defines error code handling, message interpolation, string representation,
    and dictionary serialization.

    Errors follow HTTP status semantics and are divided into two categories:

    - Usage errors (4xx): caused by invalid input, configuration issues,
      missing resources, or public API contract violations. These are
      caller-correctable and safe to expose.
    - Internal errors (5xx): caused by bugs, invariant violations, or
      unexpected framework state.

    Exceptions are also organized by domain, allowing them to be caught
    either by category (e.g. TiozinNotFoundError) or by domain
    (e.g. JobNotFoundError).

    The `retryable` class attribute indicates whether the operation may
    succeed if retried without changes. Defaults to False and should be
    True only for transient failures such as timeouts or temporarily
    unavailable resources.
    """

    message: str = "An error occurred while executing Tiozin."
    http_status: int = 500
    retryable: bool = False

    def __init__(self, message: str = None, *, code: str = None, **options) -> None:
        self.code = code or type(self).__name__
        template = message or self.message or ""

        try:
            self.message = template.format(code=self.code, **options)
        except Exception:
            self.message = template

        super().__init__(self.message)

    @classmethod
    def raise_if(cls, condition: bool, *args, **kwargs) -> Self:
        """
        Guard-style helper that raises this exception if the condition is True.
        """
        if bool(condition):
            raise cls(*args, **kwargs)
        return cls

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }

    def __str__(self) -> str:
        return self.message


class TiozinUsageError(TiozinError):
    """
    Base class for errors caused by incorrect use of the framework.

    Raised when execution fails due to invalid input, configuration,
    missing resources, or contract violations in the public API.

    Covers all callers: job YAML authors, Python API consumers, and
    plugin developers. These errors are correctable by the caller
    and safe to surface.
    """

    http_status = 400
    message = "Invalid input or configuration. Please review and try again."


class TiozinInternalError(TiozinError):
    """
    Base class for unexpected internal framework failures.

    Indicates bugs, invariant violations, or invalid internal state
    that the caller cannot correct. Should fail fast.
    """

    http_status = 500
    message = "Tiozin ran into an internal error."
