from __future__ import annotations

import pydantic as pyd

from .authoritative_definition import AuthoritativeDefinition
from .custom_property import CustomProperty
from .model import Model


class Constraint(Model):
    """
    Something AI agents must not do with a schema.

    Examples:

        ```python
        Context(
            constraints=[
                Constraint(constraint="Never expose email or phone in answers."),
            ]
        )
        ```
    """

    id: str | None = pyd.Field(
        None,
        description="Stable identifier of the constraint.",
    )
    constraint: str = pyd.Field(
        description="The text of the constraint.",
    )
    tags: list[str] | None = pyd.Field(
        None,
        description="Tags of the constraint.",
    )
    customProperties: list[CustomProperty] | None = pyd.Field(
        None,
        description="Properties that the standard does not define.",
    )
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = pyd.Field(
        None,
        description="Links to sources with more details.",
    )
