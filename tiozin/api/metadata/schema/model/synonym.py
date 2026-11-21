from __future__ import annotations

import pydantic as pyd

from .custom_property import CustomProperty
from .model import Model
from .stable_id import StableId


class Synonym(Model):
    """
    Another name for a schema or a property.

    Examples:

        ```python
        Property(
            name="customer",
            synonyms=[
                Synonym(synonym="client"),
                Synonym(synonym="cliente", locale="pt-BR"),
            ],
        )
        ```
    """

    id: StableId | None = pyd.Field(
        None,
        description="Stable identifier, unique among the synonyms around it.",
    )
    synonym: str = pyd.Field(
        description="The alternative name.",
    )
    description: str | None = pyd.Field(
        None,
        description="When or why the synonym is used.",
    )
    locale: str | None = pyd.Field(
        None,
        description="Language of the synonym, such as en-US.",
    )
    source: str | None = pyd.Field(
        None,
        description="Where the synonym comes from.",
    )
    status: str | None = pyd.Field(
        None,
        description="Lifecycle status of the synonym.",
    )
    customProperties: list[CustomProperty] | None = pyd.Field(
        None,
        description="Properties that the standard does not define.",
    )
