from __future__ import annotations

import pydantic as pyd

from .logical_type_options import LogicalTypeOptions


class ObjectOptions(LogicalTypeOptions):
    """
    Options of the object logical type.

    Examples:

        ```python
        Property(
            name="address",
            logicalType="object",
            logicalTypeOptions=ObjectOptions(required=["city"]),
        )
        ```
    """

    model_config = pyd.ConfigDict(extra="forbid")

    minProperties: int = pyd.Field(
        0,
        ge=0,
        description="Minimum number of properties of the object.",
    )
    maxProperties: int | None = pyd.Field(
        None,
        ge=0,
        description="Maximum number of properties of the object.",
    )
    required: list[str] | None = pyd.Field(
        None,
        min_length=1,
        description="Names of the properties the object must have.",
    )
