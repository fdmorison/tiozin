from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """
    Base class for Tiozin domain models.

    Applies common validation and normalization rules.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
    )


class ImmutableModel(DomainModel):
    """
    Immutable domain model.

    Represents a value object. Instances are not meant to be mutated, like events.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
    )


class UppercaseEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name: str, *_) -> str:
        return name.upper()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class LowercaseEnum(StrEnum):
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value
