from typing import Any

RESOURCE = "resource"

# ============================================================================
# Base exception
# ============================================================================


class TioException(Exception):
    """
    Base SDK exception for all Tio errors.
    """

    message = "Oops! I ran into something unexpected while running your job."

    def __init__(self, message: str = None, code: str = None) -> None:
        self.code = code or type(self).__name__
        self.message = message or self.message
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
        }

    def __str__(self):
        return f"{self.code}: {self.message}"


# ============================================================================
# High-level categories
# ============================================================================


class ValidationException(TioException):
    message = "Hmm… some of the inputs don't look quite right. Take a moment to review them."


class ExecutionException(TioException):
    message = (
        "Something went wrong while executing your pipeline. "
        "Let's take a closer look at what happened."
    )


class ConfigurationException(TioException):
    message = (
        "It looks like your configuration might be missing something or may need an adjustment."
    )


class NotFoundException(TioException):
    message = "I tried searching everywhere, but I couldn't find the resource you requested."


class AlreadyRunningException(TioException):
    message = "The `{name}` is already running. It looks like you tried to run it twice."

    def __init__(self, name: str = RESOURCE) -> None:
        super().__init__(self.message.format(name=name))


class AlreadyFinishedException(TioException):
    message = "The `{name}` has already finished. It looks like you tried to finish it twice."

    def __init__(self, name: str = RESOURCE) -> None:
        super().__init__(self.message.format(name=name))


# ============================================================================
# Job exceptions
# ============================================================================


class JobException(ExecutionException):
    message = "There was an issue with this job. Don't worry, we can figure it out."


class JobNotFoundException(NotFoundException, JobException):
    message = (
        "I looked everywhere, but I couldn't find the `{job_name}` job. "
        "Double-check its name or location."
    )

    def __init__(self, job_name: str) -> None:
        super().__init__(self.message.format(job_name=job_name))


class TransformException(ExecutionException):
    message = "I had trouble transforming the data. Maybe something came in an unexpected format?"


class InputException(ExecutionException):
    message = (
        "I couldn't read data from the input source. Are you sure it's available and accessible?"
    )


class OutputException(ExecutionException):
    message = (
        "I tried writing the data, but something prevented me from completing it. "
        "Check the destination path or permissions."
    )


class RunnerException(ExecutionException):
    message = (
        "Something went wrong while running your job. Let's rewind and check what caused this."
    )


# ============================================================================
# Schema exceptions
# ============================================================================


class SchemaException(ConfigurationException):
    message = (
        "There seems to be an issue with the schema. "
        "Maybe a field or structure isn't what I expected."
    )


class SchemaNotFoundException(NotFoundException, SchemaException):
    message = (
        "I looked for the `{schema_name}` schema, but couldn't find it. "
        "Is it defined and in the right Schema Registry?"
    )

    def __init__(self, schema_name: str) -> None:
        super().__init__(self.message.format(schema_name=schema_name))


# ============================================================================
# Plugin exceptions
# ============================================================================


class PluginException(ExecutionException):
    message = "One of the plugins had a problem. Let's check which one and what went wrong."


class PluginNotFoundException(NotFoundException, PluginException):
    message = (
        "I looked everywhere, but I couldn't find the `{plugin_name}` plugin. "
        "Did you install it or spell its name correctly?"
    )

    def __init__(self, plugin_name: str) -> None:
        super().__init__(self.message.format(plugin_name=plugin_name))
