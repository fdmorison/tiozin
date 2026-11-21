from __future__ import annotations

import pydantic as pyd

from .model import Model
from .stable_id import StableId


class AuthoritativeDefinition(Model):
    """
    A link to a source with more details, such as a glossary or a tutorial.

    Examples:

        ```python
        Property(
            name="customer_id",
            authoritativeDefinitions=[
                AuthoritativeDefinition(
                    url="https://wiki.example.com/glossary/customer",
                    type="businessDefinition",
                )
            ],
        )
        ```
    """

    id: StableId | None = pyd.Field(
        None,
        description="Stable identifier, unique among the definitions around it.",
    )
    url: str = pyd.Field(
        description="URL of the source.",
    )
    type: str = pyd.Field(
        description="Kind of source, such as businessDefinition, glossary or tutorial.",
    )
    description: str | None = pyd.Field(
        None,
        description="What the source is about.",
    )
