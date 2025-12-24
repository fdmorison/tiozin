from enum import StrEnum

from pydantic import ValidationError


class MessageTemplates(StrEnum):
    MISSING = "The required field `{field}` is missing. Please provide this field to continue."

    STRING_TYPE = (
        "The field `{field}` must be a text string. "
        "Received: `{input}`. "
        "Please provide a valid string."
    )

    INT_TYPE = (
        "The field `{field}` must be an integer. "
        "Received: `{input}`. "
        "Please provide a whole number."
    )

    INT_PARSING = (
        "I tried to convert `{input}` into an integer for the field `{field}`, "
        "but the value could not be parsed. "
        "Please verify the format."
    )

    FLOAT_TYPE = (
        "The field `{field}` must be a numeric value. "
        "Received: `{input}`. "
        "Please provide a valid number."
    )

    FLOAT_PARSING = (
        "I tried to parse `{input}` as a number for the field `{field}`, "
        "but the value could not be parsed. "
        "Please verify the format."
    )

    BOOL_TYPE = (
        "The field `{field}` must be a boolean value (true or false). "
        "Received: `{input}`. "
        "Please adjust the value."
    )

    BOOL_PARSING = (
        "I could not interpret `{input}` as a boolean value for the field `{field}`. "
        "Please use either `true` or `false`."
    )

    DICT_TYPE = (
        "The field `{field}` must be an object (dictionary). "
        "Received: `{input}`. "
        "Please check the data structure."
    )

    LIST_TYPE = (
        "The field `{field}` must be a list. Received: `{input}`. Please provide a list value."
    )

    TUPLE_TYPE = (
        "The field `{field}` must be a tuple. Received: `{input}`. Please provide a tuple value."
    )

    SET_TYPE = "The field `{field}` must be a set. Received: `{input}`. Please provide a set value."

    GREATER_THAN = (
        "The value of `{field}` must be greater than {gt}. "
        "Received: `{input}`. "
        "Please increase the value."
    )

    GREATER_THAN_EQUAL = (
        "The value of `{field}` must be greater than or equal to {ge}. "
        "Received: `{input}`. "
        "Please adjust the value."
    )

    LESS_THAN = (
        "The value of `{field}` must be less than {lt}. "
        "Received: `{input}`. "
        "Please decrease the value."
    )

    LESS_THAN_EQUAL = (
        "The value of `{field}` must be less than or equal to {le}. "
        "Received: `{input}`. "
        "Please adjust the value."
    )

    TOO_SHORT = (
        "The field `{field}` contains too few elements. "
        "Minimum required is {min_length}. "
        "Please add more items."
    )

    TOO_LONG = (
        "The field `{field}` contains too many elements. "
        "Maximum allowed is {max_length}. "
        "Please reduce the number of items."
    )

    STRING_TOO_SHORT = (
        "The field `{field}` is too short. "
        "Minimum length is {min_length} characters. "
        "Please add more characters."
    )

    STRING_TOO_LONG = (
        "The field `{field}` is too long. "
        "Maximum length is {max_length} characters. "
        "Please shorten the value."
    )

    STRING_PATTERN_MISMATCH = (
        "The value of `{field}` does not match the expected format. "
        "Please review the required pattern."
    )

    VALUE_ERROR = "The value provided for `{field}` is invalid: {msg}. Please correct the value."

    ASSERTION_ERROR = "The field `{field}` failed validation: {msg}. Please verify the value."

    LITERAL_ERROR = (
        "The field `{field}` only accepts specific literal values. "
        "Please provide one of the allowed options."
    )

    ENUM = (
        "The field `{field}` must be one of the following values: {expected}. "
        "Please choose a valid option."
    )

    EXTRA_FORBIDDEN = (
        "The field `{field}` is not expected in this context. "
        "Please remove it or review the input structure."
    )

    MODEL_TYPE = "The provided {class_name} cannot be parsed: `{input}`."

    FROZEN_FIELD = "The field `{field}` is immutable and cannot be changed after it is set."

    FROZEN_INSTANCE = (
        "This {class_name} is frozen and cannot be modified. "
        "Please create a new instance to apply changes."
    )

    DATE_TYPE = "The field `{field}` must be a valid date. Please verify the format."

    DATE_PARSING = (
        "I tried to parse the value of `{field}` as a date, "
        "but the format was invalid. "
        "Please use the format YYYY-MM-DD."
    )

    DATETIME_TYPE = "The field `{field}` must be a valid datetime value. Please verify the format."

    DATETIME_PARSING = (
        "I tried to parse the value of `{field}` as a datetime, "
        "but the format was invalid. "
        "Please use the format YYYY-MM-DD HH:MM:SS."
    )

    TIME_TYPE = "The field `{field}` must be a valid time value. Please verify the format."

    TIME_PARSING = (
        "I tried to parse the value of `{field}` as a time, "
        "but the format was invalid. "
        "Please use the format HH:MM:SS."
    )

    URL_TYPE = (
        "The field `{field}` must be a valid URL. "
        "Please include the protocol (http:// or https://)."
    )

    URL_PARSING = (
        "I tried to parse the value of `{field}` as a URL, "
        "but the format was invalid. "
        "Please verify the address."
    )

    URL_SCHEME = (
        "The URL provided in `{field}` has an invalid scheme. Please use http:// or https://."
    )

    UUID_TYPE = "The field `{field}` must be a valid UUID. Please verify the format."

    UUID_PARSING = (
        "I tried to parse the value of `{field}` as a UUID, "
        "but the format was invalid. "
        "Please provide a valid UUID."
    )

    FALLBACK = "The value provided for `{field}` is invalid: {msg}."

    @staticmethod
    def format_friendly_message(error: ValidationError) -> list[str]:
        """
        Format Pydantic validation error into user-friendly messages.
        """
        messages = []

        for err in error.errors(include_context=True, include_input=True):
            context = {
                **err,
                **err.get("ctx", {}),
                "field": ".".join(str(loc) for loc in err.get("loc", ["unknown"])),
            }
            try:
                template = MessageTemplates[err["type"].upper()]
                formatted = template.format(**context)
            except (KeyError, ValueError):
                template = MessageTemplates.FALLBACK
                formatted = template.format(**context)

            messages.append(formatted)

        return messages
