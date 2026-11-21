from __future__ import annotations

from typing import Literal

import pydantic as pyd

from .logical_type_options import LogicalTypeOptions


class NumberOptions(LogicalTypeOptions):
    """
    Options of the number logical type.

    The standard declares i32 as the default format, but only accepts f32 and
    f64, so the format has no default here.

    Examples:

        ```python
        Property(
            name="price",
            logicalType="number",
            logicalTypeOptions=NumberOptions(format="f64", minimum=0, multipleOf=0.01),
        )
        ```
    """

    model_config = pyd.ConfigDict(extra="forbid")

    format: Literal["f32", "f64"] | None = pyd.Field(
        None,
        description="Size of the values, named as the Rust float types.",
    )
    multipleOf: int | float | None = pyd.Field(
        None,
        gt=0,
        description="Every value is a multiple of this number.",
    )
    minimum: int | float | None = pyd.Field(
        None,
        description="Every value is greater than or equal to this one.",
    )
    exclusiveMinimum: int | float | None = pyd.Field(
        None,
        description="Every value is greater than this one.",
    )
    maximum: int | float | None = pyd.Field(
        None,
        description="Every value is less than or equal to this one.",
    )
    exclusiveMaximum: int | float | None = pyd.Field(
        None,
        description="Every value is less than this one.",
    )
