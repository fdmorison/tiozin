from __future__ import annotations

from typing import Literal

import pydantic as pyd

from .custom_property import CustomProperty
from .model import Model


class Relationship(Model):
    """
    A link between properties, such as a foreign key.

    At the schema level both ends are given. At the property level only the
    target is given, because the source is the property itself.

    Since from is a Python keyword, pass it through a dict, or set from_.

    Examples:

        ```python
        Schema(
            name="orders",
            relationships=[
                Relationship(**{"from": "orders.customer_id", "to": "customers.id"}),
            ],
        )

        Property(
            name="customer_id",
            relationships=[Relationship(to="customers.id")],
        )

        Relationship(
            **{
                "from": ["orders.country", "orders.store"],
                "to": ["stores.country", "stores.code"],
            }
        )
        ```
    """

    id: str | None = pyd.Field(
        None,
        description="Stable identifier, unique among the relationships around it.",
    )
    type: Literal["foreignKey"] = pyd.Field(
        "foreignKey",
        description="Kind of relationship.",
    )
    from_: str | list[str] | None = pyd.Field(
        None,
        alias="from",
        description="Source property, or source properties of a composite key.",
    )
    to: str | list[str] = pyd.Field(
        description="Target property, or target properties of a composite key.",
    )
    customProperties: list[CustomProperty] | None = pyd.Field(
        None,
        description="Properties that the standard does not define.",
    )
