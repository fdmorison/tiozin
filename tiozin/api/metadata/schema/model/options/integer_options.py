from __future__ import annotations

from typing import Literal

import pydantic as pyd

from .logical_type_options import LogicalTypeOptions


class IntegerOptions(LogicalTypeOptions):
    """
    Options of the integer logical type.

    Examples:

        ```python
        Property(
            name="age",
            logicalType="integer",
            logicalTypeOptions=IntegerOptions(format="u8", minimum=0, maximum=150),
        )
        ```
    """

    model_config = pyd.ConfigDict(extra="forbid")

    format: Literal[
        "i8",
        "i16",
        "i32",
        "i64",
        "i128",
        "u8",
        "u16",
        "u32",
        "u64",
        "u128",
    ] = pyd.Field(
        "i32",
        description="Size and sign of the values, named as the Rust integer types.",
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
