from typing import Any

from pydantic import ValidationError

RESOURCE = "resource"

# ============================================================================
# Base exception
# ============================================================================


class TioException(Exception):
    """
    Base SDK exception for all Tiozin errors.
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


class JobManifestException(NotFoundException, JobException):
    message = "The content is not a valid Job Manifest"

    def __init__(self, message: str = None, job_name: str = None) -> None:
        if job_name and not message:
            message = self.message.format(job_name=job_name)
        super().__init__(message or self.message)

    @classmethod
    def from_pydantic(cls, error: ValidationError, job_name: str = None):
        templates = {
            "missing": "Field `{field}` is required",
            "string_type": "Field `{field}` must be string: {input}",
            "int_type": "Field `{field}` must be integer: {input}",
            "int_parsing": "Field `{field}` must be integer: {input}",
            "float_type": "Field `{field}` must be a number: {input}",
            "float_parsing": "Field `{field}` must be a number: {input}",
            "bool_type": "Field `{field}` must be true or false: {input}",
            "bool_parsing": "Field `{field}` must be true or false: {input}",
            "dict_type": "Field `{field}` must be an object: {input}",
            "list_type": "Field `{field}` must be a list: {input}",
            "tuple_type": "Field `{field}` must be a tuple: {input}",
            "set_type": "Field `{field}` must be a set: {input}",
            "greater_than": "Field `{field}` must be greater than {gt}: {input}",
            "greater_than_equal": "Field `{field}` must be greater than or equal to {ge}: {input}",
            "less_than": "Field `{field}` must be less than {lt}: {input}",
            "less_than_equal": "Field `{field}` must be less than or equal to {le}: {input}",
            "too_short": "Field `{field}` is too short (minimum {min_length}): {input}",
            "too_long": "Field `{field}` is too long (maximum {max_length}): {input}",
            "string_too_short": "Field `{field}` must have at least {min_length} chars: {input}",
            "string_too_long": "Field `{field}` must have at most {max_length} chars: {input}",
            "string_pattern_mismatch": "Field `{field}` format is invalid: {input}",
            "value_error": "Field `{field}`: {msg}",
            "assertion_error": "Field `{field}`: {msg}",
            "literal_error": "Field `{field}` must be one of the allowed literal values",
            "enum": "Field `{field}` must be one of: {expected}",
            "extra_forbidden": "Unexpected field `{field}` is not allowed",
            "model_type": f"{cls.message}. Unexpected content: `{{input}}`",
            "frozen_field": "Field `{field}` is immutable and cannot be changed",
            "frozen_instance": "The Job Manifest instance is frozen and cannot be modified",
            "date_type": "Field `{field}` must be a valid date",
            "date_parsing": "Field `{field}` could not be parsed as a date",
            "datetime_type": "Field `{field}` must be a valid datetime",
            "datetime_parsing": "Field `{field}` could not be parsed as a datetime",
            "time_type": "Field `{field}` must be a valid time",
            "time_parsing": "Field `{field}` could not be parsed as a time",
            "url_type": "Field `{field}` must be a valid URL",
            "url_parsing": "Field `{field}` could not be parsed as a URL",
            "url_scheme": "Field `{field}` has an invalid URL scheme",
            "uuid_type": "Field `{field}` must be a valid UUID",
            "uuid_parsing": "Field `{field}` could not be parsed as a UUID",
        }

        messages = []
        for err in error.errors():
            name = ".".join(str(loc) for loc in err["loc"])
            type = err["type"]
            template = templates.get(type, "{field}: {msg}")
            context = {
                "field": name,
                "msg": err.get("msg", cls.message),
                "input": err.get("input"),
                **err.get("ctx", {}),
            }
            try:
                messages.append(template.format(**context))
            except KeyError:
                messages.append(f"{name}: {context['msg']}")

        # return error
        return cls(message="\n".join(messages), job_name=job_name)


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
