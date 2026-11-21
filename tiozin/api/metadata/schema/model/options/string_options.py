from __future__ import annotations

import pydantic as pyd

from .logical_type_options import LogicalTypeOptions


class StringOptions(LogicalTypeOptions):
    """
    Options of the string logical type.

    Examples:

        ```python
        Property(
            name="email",
            logicalType="string",
            logicalTypeOptions=StringOptions(maxLength=254, format="email"),
        )

        Property(
            name="zip_code",
            logicalType="string",
            logicalTypeOptions=StringOptions(pattern="^[0-9]{5}-[0-9]{3}$"),
        )
        ```
    """

    model_config = pyd.ConfigDict(extra="forbid")

    minLength: int | None = pyd.Field(
        None,
        ge=0,
        description="Minimum length of the string.",
    )
    maxLength: int | None = pyd.Field(
        None,
        ge=0,
        description="Maximum length of the string.",
    )
    pattern: str | None = pyd.Field(
        None,
        description="Regular expression the string must match, in ECMA-262 syntax.",
    )
    format: str | None = pyd.Field(
        None,
        description="What the string holds, such as email, uuid or uri.",
    )
