from __future__ import annotations

import pydantic as pyd

from .date_options import DateOptions

DEFAULT_TIMEZONE = "Etc/UTC"


class TimestampOptions(DateOptions):
    """
    Options of the timestamp and time logical types.

    Examples:

        ```python
        Property(
            name="created_at",
            logicalType="timestamp",
            logicalTypeOptions=TimestampOptions(timezone=True),
        )

        Property(
            name="opens_at",
            logicalType="time",
            logicalTypeOptions=TimestampOptions(
                format="HH:mm",
                defaultTimezone="America/Sao_Paulo",
            ),
        )
        ```
    """

    timezone: bool | None = pyd.Field(
        None,
        description="Whether the values carry their timezone.",
    )
    defaultTimezone: str = pyd.Field(
        DEFAULT_TIMEZONE,
        description="Timezone of the values that do not carry one.",
    )
