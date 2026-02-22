from __future__ import annotations

from typing import Any, Self

from pydantic import ValidationError
from ruamel.yaml.error import MarkedYAMLError

from tiozin.utils import human_join


# ============================================================================
# Layer 1: Base Exceptions
# ============================================================================
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
        return f"{self.code}: {self.message}"


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
    message = "Tiozin ran into an unexpected internal error."


# ============================================================================
# Layer 2: Categorical exceptions
# ============================================================================
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


# ============================================================================
# Layer 3: Domain Exceptions - Manifest
# ============================================================================
class ManifestError(TiozinInputError):
    """
    Raised when a declarative manifest fails parsing or validation.

    Applies to any resource defined via YAML or Pydantic models, not
    exclusively to jobs. Factory methods are provided for the most
    common error sources.
    """

    message = "Invalid manifest `{manifest}`: {msg}"

    def __init__(self, manifest: str, message: str) -> None:
        super().__init__(manifest=manifest, msg=message)

    @classmethod
    def from_pydantic(cls, manifest: str, error: ValidationError) -> Self:
        from .utils.messages import MessageTemplates

        messages = MessageTemplates.format_friendly_message(error)
        message = human_join(messages)
        return cls(manifest, message)

    @classmethod
    def from_ruamel(cls, manifest: str, error: MarkedYAMLError) -> Self:
        info = str(error.problem).capitalize()
        line = str(error.problem_mark).strip()
        message = f"{info} {line}"
        return cls(manifest, message)


# ============================================================================
# Layer 3: Domain Exceptions - Job
# ============================================================================
class JobError(TiozinUsageError):
    """
    Base exception for job-related errors.
    """

    message = "An error occurred while processing the job."


class JobNotFoundError(JobError, TiozinNotFoundError):
    """
    Raised when a job cannot be found.
    """

    message = "Job `{name}` not found."

    def __init__(self, message: str = None, *, name: str = None) -> None:
        super().__init__(message, name=name)

    @classmethod
    def raise_if(cls, condition: bool, message: str = None, *, name: str = None) -> type[Self]:
        if condition:
            raise cls(message, name=name)
        return cls


class JobAlreadyExistsError(JobError, TiozinConflictError):
    """
    Raised when a job with the same name already exists.
    """

    message = "The job `{name}` already exists."

    def __init__(self, message: str = None, *, name: str) -> None:
        super().__init__(
            message,
            name=name,
        )

    @classmethod
    def raise_if(cls, condition: bool, message: str = None, *, name: str) -> type[Self]:
        if condition:
            raise cls(message, name=name)
        return cls


# ============================================================================
# Layer 3: Domain Exceptions - Schema
# ============================================================================
class SchemaError(TiozinUsageError):
    """
    Base exception for schema registry errors.
    """

    message = "The schema validation failed."


class SchemaViolationError(SchemaError, TiozinInputError):
    """
    Raised when an input violates one or more schema constraints.
    """

    message = "The input violates one or more schema constraints."


class SchemaNotFoundError(SchemaError, TiozinNotFoundError):
    """
    Raised when a schema subject cannot be found in the registry.
    """

    message = "Schema `{subject}` not found in the registry."

    def __init__(self, subject: str) -> None:
        super().__init__(subject=subject)

    @classmethod
    def raise_if(cls, condition: bool, subject: str) -> type[Self]:
        if condition:
            raise cls(subject)
        return cls


# ============================================================================
# Layer 3: Domain Exceptions - Plugin
# ============================================================================
class PluginError(TiozinUsageError):
    """
    Base exception for plugin discovery, resolution, and loading errors.
    """

    message = "The Tiozin plugin discovery, resolution or load failed."


class PluginNotFoundError(PluginError, TiozinNotFoundError):
    """
    Raised when a Tiozin plugin cannot be found for the given name.
    """

    message = "Tiozin `{name}` not found. Ensure its family is installed."

    def __init__(self, *, name: str = None) -> None:
        super().__init__(name=name)

    @classmethod
    def raise_if(cls, condition: bool, *, name: str = None) -> type[Self]:
        if condition:
            raise cls(name=name)
        return cls


class PluginConflictError(PluginError, TiozinConflictError):
    """
    Raised when a Tiozin name matches multiple registered plugins.
    """

    message = (
        "The Tiozin name '{name}' matches multiple registered Tiozin plugins. "
        "Available provider-qualified options are: {candidates}. "
        "You can disambiguate by specifying the provider-qualified name "
        "or the fully qualified Python class path."
    )

    def __init__(self, *, name: str = None, candidates: list[str] = None) -> None:
        super().__init__(
            name=name,
            candidates=human_join(candidates or []),
        )

    @classmethod
    def raise_if(
        cls,
        condition: bool,
        *,
        name: str = None,
        candidates: list[str] = None,
    ) -> type[Self]:
        if condition:
            raise cls(name=name, candidates=candidates)
        return cls


# ============================================================================
# Layer 4: Runtime State Errors
# ============================================================================
class AlreadyRunningError(TiozinConflictError):
    """
    Raised when an operation is attempted on a resource that is already running.
    """

    retryable = True
    message = "The {name} is already running."

    def __init__(self, name: str = None) -> None:
        super().__init__(name=name or "resource")

    @classmethod
    def raise_if(cls, condition: bool, name: str = None) -> type[Self]:
        if condition:
            raise cls(name)
        return cls


class AlreadyFinishedError(TiozinConflictError):
    """
    Raised when an operation is attempted on a resource that has already finished.
    """

    message = "The {name} has already finished."

    def __init__(self, name: str = None) -> None:
        super().__init__(name=name or "resource")

    @classmethod
    def raise_if(cls, condition: bool, name: str = None) -> type[Self]:
        if condition:
            raise cls(name)
        return cls


# ============================================================================
# Layer 4: Policy and Validation Errors
# ============================================================================
class PolicyViolationError(TiozinInputError):
    """
    Raised when execution is denied due to a policy violation.
    """

    message = "{policy}: {detail}."

    def __init__(self, policy: type, message: str = None) -> None:
        super().__init__(policy=policy.__name__, detail=message or "Execution was denied")

    @classmethod
    def raise_if(cls, condition: bool, policy: type, message: str = None) -> type[Self]:
        if condition:
            raise cls(policy, message)
        return cls


class RequiredArgumentError(TiozinInputError):
    """
    Raised when a required argument is null, empty, or absent.
    """

    NULL_OR_EMPTY = [None, "", [], {}, tuple(), set()]

    def __init__(self, message: str, **options) -> None:
        super().__init__(message, **options)

    @classmethod
    def raise_if_missing(
        cls,
        disable_: bool = False,
        exclude_: list[str] | None = None,
        **fields,
    ) -> Self:
        """
        Validates that required fields are not null or empty.

        Args:
            disable_: If True, skip validation entirely
            exclude_: List of field names to skip validation
            **fields: Field name-value pairs to validate

        Raises:
            RequiredArgumentError: If any required field is missing or empty
        """
        if disable_:
            return

        exclude_ = exclude_ or []
        missing = [
            argument
            for argument, value in fields.items()
            if value in cls.NULL_OR_EMPTY and argument not in exclude_
        ]
        if missing:
            fields_str = ", ".join(f"'{f}'" for f in missing)
            raise cls(f"Missing required fields: {fields_str}")
        return cls


# ============================================================================
# Layer 4: Internal Errors
# ============================================================================
class ProxyError(TiozinInternalError):
    """
    Raised when the @tioproxy decorator is misused.

    Indicates a provider implementation bug, such as applying the decorator
    more than once or registering a class that does not inherit from
    ``wrapt.ObjectProxy``.
    """

    message = "The @tioproxy decorator was used incorrectly."


class NotInitializedError(TiozinInternalError):
    """
    Raised when a resource is accessed before its initialization is complete.

    Indicates an invalid execution order or lifecycle contract violation.
    Not a user configuration issue — callers should provide a descriptive
    message identifying which resource was accessed prematurely.
    """

    message = "Resource was accessed before being initialized."

    def __init__(self, message: str = None) -> None:
        super().__init__(message)

    @classmethod
    def raise_if(cls, condition: bool, message: str = None) -> type[Self]:
        if condition:
            raise cls(message)
        return cls


class AccessViolationError(TiozinInternalError):
    """
    Raised when runtime-reserved methods are invoked directly by plugin code.

    Setup and teardown are owned exclusively by the Tiozin runtime. Calling
    them directly from within a plugin or proxy is a provider implementation
    bug — equivalent to accessing a private method in a managed framework.
    """

    message = "{name} invoked a method reserved for the Tiozin runtime."

    def __init__(self, name: str) -> None:
        super().__init__(name=name)

    @classmethod
    def raise_if(cls, condition: bool, name: str) -> type[Self]:
        if condition:
            raise cls(name)
        return cls
