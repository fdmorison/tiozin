from __future__ import annotations

import pydantic as pyd

from .constraint import Constraint
from .model import Model
from .verified_statement import VerifiedStatement


class Context(Model):
    """
    Guidance for AI agents and tools on how to use a schema.

    A schema also accepts the instructions alone, as a string.

    Examples:

        ```python
        Schema(
            name="orders",
            context=Context(
                instructions="One row per order. Amounts are in cents.",
                verifiedStatements=[
                    VerifiedStatement(
                        question="How do I get the revenue of a day?",
                        answer="Sum amount where status is paid.",
                    )
                ],
                constraints=[Constraint(constraint="Never join on email.")],
            ),
        )

        Schema(name="orders", context="One row per order.")
        ```
    """

    instructions: str | None = pyd.Field(
        None,
        description="Guidance in natural language.",
    )
    verifiedStatements: list[VerifiedStatement] | None = pyd.Field(
        None,
        description="Questions about the schema, with verified answers when there are any.",
    )
    constraints: list[Constraint] | None = pyd.Field(
        None,
        description="What AI agents must not do with the schema.",
    )
