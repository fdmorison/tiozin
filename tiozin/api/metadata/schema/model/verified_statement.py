from __future__ import annotations

import pydantic as pyd

from .authoritative_definition import AuthoritativeDefinition
from .custom_property import CustomProperty
from .model import Model


class VerifiedStatement(Model):
    """
    A question about a schema, with its verified answer when there is one.

    Examples:

        ```python
        Context(
            verifiedStatements=[
                VerifiedStatement(
                    question="Which orders count as sales?",
                    answer="Orders whose status is paid or shipped.",
                ),
                VerifiedStatement(question="Are refunds included?"),
            ]
        )
        ```
    """

    id: str | None = pyd.Field(
        None,
        description="Stable identifier of the statement.",
    )
    question: str = pyd.Field(
        description="The question.",
    )
    answer: str | None = pyd.Field(
        None,
        description="The verified answer.",
    )
    tags: list[str] | None = pyd.Field(
        None,
        description="Tags of the statement.",
    )
    customProperties: list[CustomProperty] | None = pyd.Field(
        None,
        description="Properties that the standard does not define.",
    )
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = pyd.Field(
        None,
        description="Links to sources with more details.",
    )
