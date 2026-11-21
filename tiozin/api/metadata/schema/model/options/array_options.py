from __future__ import annotations

import pydantic as pyd

from .logical_type_options import LogicalTypeOptions


class ArrayOptions(LogicalTypeOptions):
    """
    Options of the array logical type.

    Examples:

        ```python
        Property(
            name="tags",
            logicalType="array",
            items=Property(logicalType="string"),
            logicalTypeOptions=ArrayOptions(minItems=1, maxItems=10, uniqueItems=True),
        )
        ```
    """

    model_config = pyd.ConfigDict(extra="forbid")

    minItems: int = pyd.Field(
        0,
        ge=0,
        description="Minimum number of items of the array.",
    )
    maxItems: int | None = pyd.Field(
        None,
        ge=0,
        description="Maximum number of items of the array.",
    )
    uniqueItems: bool = pyd.Field(
        False,
        description="Whether every item of the array is different from the others.",
    )
