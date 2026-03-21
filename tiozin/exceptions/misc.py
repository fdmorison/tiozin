from __future__ import annotations

from typing import Self

from pydantic import ValidationError
from ruamel.yaml.error import MarkedYAMLError

from tiozin.exceptions.base import TiozinInternalError
from tiozin.exceptions.categories import TiozinConflictError, TiozinInputError
from tiozin.utils import human_join


class ManifestError(TiozinInputError):
    """
    Raised when a declarative manifest fails parsing or validation.

    Applies to any resource defined via YAML or Pydantic models, not
    exclusively to jobs. Factory methods are provided for the most
    common error sources.
    """

    message = "Invalid `{manifest}`: {msg}"

    def __init__(self, manifest: str, message: str) -> None:
        super().__init__(manifest=manifest, msg=message)

    @classmethod
    def from_pydantic(cls, manifest: str, error: ValidationError) -> Self:
        from tiozin.utils.messages import MessageTemplates

        messages = MessageTemplates.format_friendly_message(error)
        message = human_join(messages)
        return cls(manifest, message)

    @classmethod
    def from_ruamel(cls, manifest: str, error: MarkedYAMLError) -> Self:
        info = str(error.problem).capitalize()
        line = str(error.problem_mark).strip()
        message = f"{info} {line}"
        return cls(manifest, message)


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
