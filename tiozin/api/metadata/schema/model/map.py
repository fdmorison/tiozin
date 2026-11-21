from __future__ import annotations

from typing import TYPE_CHECKING

import pydantic as pyd

from .model import Model

if TYPE_CHECKING:
    from .property import Property


class Map(Model):
    """
    The key and the value of a map property.

    Each side is a `Property` without a name. `Schema.map` builds one for you.

    Examples:

        ```python
        Property(
            name="scores",
            logicalType="map",
            map=Map(
                key=Property(logicalType="string"),
                value=Property(logicalType="integer"),
            ),
        )

        schema.map("scores", value="integer")
        ```
    """

    key: Property | None = pyd.Field(
        None,
        description="Definition of the keys of the map.",
    )
    value: Property | None = pyd.Field(
        None,
        description="Definition of the values of the map.",
    )
