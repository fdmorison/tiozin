from __future__ import annotations

import pydantic as pyd

from .authoritative_definition import AuthoritativeDefinition
from .custom_property import CustomProperty
from .model import Model
from .stable_id import StableId


class EnumValue(Model):
    """
    One of the values a property is allowed to have.

    Examples:

        ```python
        Property(
            name="status",
            logicalType="string",
            enum=[
                EnumValue(value="A", label="Active"),
                EnumValue(value="C", label="Cancelled", description="Closed by the customer."),
            ],
        )
        ```
    """

    id: StableId | None = pyd.Field(
        None,
        description="Stable identifier, unique among the values around it.",
    )
    value: str | int | float | bool | None = pyd.Field(
        description="The allowed value.",
    )
    label: str | None = pyd.Field(
        None,
        description="Name of the value for people to read.",
    )
    description: str | None = pyd.Field(
        None,
        description="What the value means.",
    )
    tags: list[str] | None = pyd.Field(
        None,
        description="Tags of the value.",
    )
    customProperties: list[CustomProperty] | None = pyd.Field(
        None,
        description="Properties that the standard does not define.",
    )
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = pyd.Field(
        None,
        description="Links to sources with more details.",
    )
