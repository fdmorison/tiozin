from __future__ import annotations

import pydantic as pyd

from .logical_type_options import LogicalTypeOptions


class DateOptions(LogicalTypeOptions):
    """
    Options of the date logical type.

    Examples:

        ```python
        Property(
            name="birth_date",
            logicalType="date",
            logicalTypeOptions=DateOptions(format="yyyy-MM-dd", minimum="1900-01-01"),
        )
        ```
    """

    model_config = pyd.ConfigDict(extra="forbid")

    format: str | None = pyd.Field(
        None,
        description="Format of the date, in JDK DateTimeFormatter syntax, such as yyyy-MM-dd.",
    )
    minimum: str | None = pyd.Field(
        None,
        description="Every value is greater than or equal to this one.",
    )
    exclusiveMinimum: str | None = pyd.Field(
        None,
        description="Every value is greater than this one.",
    )
    maximum: str | None = pyd.Field(
        None,
        description="Every value is less than or equal to this one.",
    )
    exclusiveMaximum: str | None = pyd.Field(
        None,
        description="Every value is less than this one.",
    )
