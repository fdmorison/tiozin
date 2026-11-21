from __future__ import annotations

from typing import Any

import pydantic as pyd

from .model import Model
from .stable_id import StableId


class CustomProperty(Model):
    """
    A property that the standard does not define, as a name and a value.

    Use it for attributes that have no place in the standard, such as a
    setting of a specific tool.

    Examples:

        ```python
        Property(
            name="id",
            logicalType="string",
            customProperties=[
                CustomProperty(property="retentionDays", value=90),
                CustomProperty(property="avro.java.string", value="String", vendor="avro"),
            ],
        )
        ```
    """

    id: StableId | None = pyd.Field(
        None,
        description="Stable identifier, unique among the custom properties around it.",
    )
    property: str = pyd.Field(
        description="Name of the custom property, in camel case.",
    )
    value: Any = pyd.Field(
        description="Value of the custom property.",
    )
    description: str | None = pyd.Field(
        None,
        description="What the custom property means.",
    )
    vendor: str | None = pyd.Field(
        None,
        description="Vendor or tool that owns the custom property.",
    )
