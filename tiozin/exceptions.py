from typing import Any, Optional, Self

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

    def __init__(self, message: Optional[str] = None, code: Optional[str] = None) -> None:
        self.code = code or type(self).__name__
        self.message = message or self.message
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
        super().__init__(self.message.format(job_name=job_name))


class JobAlreadyExistsError(JobError, ConflictError):
    """Raised when a job operation conflicts with its current state."""

    message = "The job `{job_name}` already exists."

    def __init__(self, job_name: str, reason: str = None) -> None:
        msg = self.message.format(job_name=job_name)
        if reason:
            msg = f"{msg} {reason}."
        super().__init__(msg)


class JobManifestError(JobError, InvalidInputError):
    """Raised when job manifest validation fails."""

    def __init__(self, message: str, job: str = None) -> None:
        message = f"{job}: {message}" if job else message
        super().__init__(message)

    @classmethod
    def from_pydantic(cls, error: ValidationError, job: str = None) -> Self:
        messages = MessageTemplates.format_friendly_message(error)
        messages = ". ".join(messages)
        return cls(message=messages, job=job)

    @classmethod
    def from_ruamel(cls, error: MarkedYAMLError, job: str = None) -> Self:
        info = str(error.problem).capitalize()
        line = str(error.problem_mark).strip()
        message = f"{info} {line}"
        return cls(message=message, job=job)


# ============================================================================
# Layer 3: Domain Exceptions - Schema
# ============================================================================
class SchemaError(InvalidInputError):
    """Base exception for schema-related errors."""

    message = "The schema is invalid or contains errors."


class SchemaViolationError(SchemaError, InvalidInputError):
    """
    Raised when the input violates one or more schema constraints.
    """

    message = "The input violates the expected schema."


class SchemaNotFoundError(SchemaError, NotFoundError):
    """Raised when a schema cannot be found in the registry."""

    message = "Schema `{subject}` not found in the registry."

    def __init__(self, subject: str) -> None:
        super().__init__(self.message.format(subject=subject))


# ============================================================================
# Layer 3: Domain Exceptions - Plugin
# ============================================================================
class PluginError(TiozinError):
    """Base exception for unexpected plugin-related errors."""

    message = "An unexpected error occurred in one of the plugins."


class PluginNotFoundError(PluginError, NotFoundError):
    """Raised when a plugin cannot be found or loaded."""

    message = "Plugin `{plugin_name}` not found."

    def __init__(self, plugin_name: str) -> None:
        super().__init__(self.message.format(plugin_name=plugin_name))


class InvalidPluginError(PluginError, InvalidInputError):
    """Raised when plugin configuration is invalid."""

    message = "The configuration for plugin `{plugin_name}` is invalid."

    def __init__(self, plugin_name: str, details: str = None) -> None:
        msg = self.message.format(plugin_name=plugin_name)
        if details:
            msg = f"{msg} {details}"
        super().__init__(msg)


# ============================================================================
# Layer 3: Domain Exceptions - Misc
# ============================================================================
class AlreadyRunningError(ConflictError):
    message = "The `{name}` is already running."

    def __init__(self, name: str = RESOURCE) -> None:
        super().__init__(self.message.format(name=name))


class AlreadyFinishedError(ConflictError):
    message = "The `{name}` has already finished."

    def __init__(self, name: str = RESOURCE) -> None:
        super().__init__(self.message.format(name=name))
