from typing import Any, Self

from pydantic import ValidationError
from ruamel.yaml.error import MarkedYAMLError

from .utils.messages import MessageTemplates

RESOURCE = "resource"


# ============================================================================
# Layer 1: Base Exceptions
# ============================================================================
class TiozinErrorMixin:
    """
    Shared logic for Tiozin exceptions.

    Provides standardized error code handling, message resolution,
    string representation, and dictionary serialization.
    """

    message: str = None
    http_status: int = None

    def __init__(self, message: str | None = None, *, code: str | None = None, **options) -> None:
        self.code = code or type(self).__name__
        self.message = (message or self.message).format(code=code, **options)
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.http_status:
            result["http_status"] = self.http_status
        return result

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class TiozinError(TiozinErrorMixin, Exception):
    """
    Base exception for all expected Tiozin errors.

    Raised for handleable errors caused by invalid input, configuration issues,
    missing resources, or contract violations that users can fix.
    """

    http_status = 400
    message = "Tiozin couldn't proceed due to an issue."


class TiozinUnexpectedError(TiozinErrorMixin, RuntimeError):
    """
    Base exception for unexpected/internal errors that should not be handled.

    Use this for bugs, assertion failures, third-party library errors, runtime failures
    that indicate system/code issues, and truly unexpected conditions that should
    propagate and crash.
    """

    http_status = 500
    message = "Tiozin ran into an unexpected internal error."


# ============================================================================
# Layer 2: Categorical exceptions
# ============================================================================
class NotFoundError(TiozinError):
    """
    Raised when a requested resource cannot be found.
    """

    http_status = 404
    message = "The requested resource could not be found."


class ConflictError(TiozinError):
    """
    Raised when an operation conflicts with the current state of a resource.
    """

    http_status = 409
    message = "The operation conflicts with the current state of the resource."


class InvalidInputError(TiozinError):
    """
    Raised when resource fails validation rules.
    """

    http_status = 422
    message = "The input failed validation. Please review and correct the errors."


class OperationTimeoutError(TiozinError):
    """
    Raised when an operation exceeds its time limit.
    """

    http_status = 408
    message = "The operation exceeded the time limit and timed out."


class ForbiddenError(TiozinError):
    """
    Raised when access to a resource or operation is forbidden.
    """

    http_status = 403
    message = "You are not allowed to perform this operation."


# ============================================================================
# Layer 3: Domain Exceptions - Job
# ============================================================================
class JobError(TiozinError):
    """Base exception for unexpected job-related errors."""

    message = "An unexpected error occurred while processing the job."


class JobNotFoundError(JobError, NotFoundError):
    """Raised when a job cannot be found."""

    message = "Job `{job_name}` not found."

    def __init__(self, job_name: str) -> None:
        super().__init__(job_name=job_name)


class JobAlreadyExistsError(JobError, ConflictError):
    message = "The job `{job_name}` already exists."

    def __init__(self, job_name: str, reason: str = None) -> None:
        super().__init__(
            f"{self.message} {reason}." if reason else None,
            job_name=job_name,
        )


class ManifestError(JobError, InvalidInputError):
    message = "Invalid manifest for `{name}`: {detail}"

    def __init__(self, message: str, name: str) -> None:
        super().__init__(name=name, detail=message)

    @classmethod
    def from_pydantic(cls, error: ValidationError, name: str = None) -> Self:
        messages = MessageTemplates.format_friendly_message(error)
        messages = ". ".join(messages)
        return cls(message=messages, name=name or "manifest")

    @classmethod
    def from_ruamel(cls, error: MarkedYAMLError, name: str = None) -> Self:
        info = str(error.problem).capitalize()
        line = str(error.problem_mark).strip()
        message = f"{info} {line}"
        return cls(message=message, name=name)


# ============================================================================
# Layer 3: Domain Exceptions - Schema
# ============================================================================
class SchemaError(InvalidInputError):
    message = "The schema validation failed."


class SchemaViolationError(SchemaError, InvalidInputError):
    message = "The input violates one or more schema constraints."


class SchemaNotFoundError(SchemaError, NotFoundError):
    message = "Schema `{subject}` not found in the registry."

    def __init__(self, subject: str) -> None:
        super().__init__(subject=subject)


# ============================================================================
# Layer 3: Domain Exceptions - Plugin
# ============================================================================
class PluginError(TiozinError):
    message = "The plugin discovery, resolution or load failed."


class PluginNotFoundError(PluginError, NotFoundError):
    message = "Plugin `{plugin_name}` not found."
    detail = "Ensure its provider is installed and loads correctly via entry points"

    def __init__(self, plugin_name: str, detail: str = None) -> None:
        detail = detail or self.detail
        super().__init__(f"{self.message} {detail}.", plugin_name=plugin_name)


class AmbiguousPluginError(PluginError, ConflictError):
    message = (
        "The plugin name '{plugin_name}' matches multiple registered plugins. "
        "Available provider-qualified options are: {candidates}. "
        "You can disambiguate by specifying the provider-qualified name "
        "or the fully qualified Python class path."
    )

    def __init__(self, plugin_name: str, candidates: list[str] = None) -> None:
        super().__init__(
            plugin_name=plugin_name,
            candidates=", ".join(candidates or []),
        )


class PluginKindError(PluginError, InvalidInputError):
    message = "Plugin '{plugin_name}' cannot be used as '{plugin_kind}'."

    def __init__(self, plugin_name: str, plugin_kind: type) -> None:
        super().__init__(
            plugin_name=plugin_name,
            plugin_kind=plugin_kind.__name__,
        )


class PluginAccessForbiddenError(PluginError, ForbiddenError):
    """
    Raised when access to a plugin's lifecycle methods is attempted outside of
    Tiozin's runtime control.

    This error indicates an attempt to directly invoke setup or teardown on a
    plugin, which are exclusively managed by the Tiozin runtime.
    """

    message = (
        "Access to {plugin} lifecycle methods is forbidden. "
        "Setup and teardown are managed by the Tiozin runtime."
    )

    def __init__(self, plugin: Any) -> None:
        super().__init__(plugin=plugin)


class PluginProxyError(PluginError):
    """Base exception for proxy-related errors."""

    message = "Failed to apply proxy to resource."


# ============================================================================
# Layer 4: Domain Exceptions - Misc
# ============================================================================
class AlreadyRunningError(ConflictError):
    message = "The `{name}` is already running."

    def __init__(self, name: str = RESOURCE) -> None:
        super().__init__(self.message.format(name=name))


class AlreadyFinishedError(ConflictError):
    message = "The `{name}` has already finished."

    def __init__(self, name: str = RESOURCE) -> None:
        super().__init__(name=name)


class PolicyViolationError(InvalidInputError):
    """
    Raised when execution is denied due to a policy violation.
    """

    message = "{policy}: {detail}."

    def __init__(self, policy: type, message: str = None) -> None:
        super().__init__(policy=policy.__name__, detail=message or "Execution was denied")


class RequiredArgumentError(InvalidInputError):
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
