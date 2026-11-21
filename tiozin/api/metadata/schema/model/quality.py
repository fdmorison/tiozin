from __future__ import annotations

from typing import Any, Literal, Self

import pydantic as pyd

from ..exceptions import SchemaError
from .authoritative_definition import AuthoritativeDefinition
from .custom_property import CustomProperty
from .model import Model
from .stable_id import StableId

OPERATORS = (
    "mustBe",
    "mustNotBe",
    "mustBeGreaterThan",
    "mustBeGreaterOrEqualTo",
    "mustBeLessThan",
    "mustBeLessOrEqualTo",
    "mustBeBetween",
    "mustNotBeBetween",
)


class Quality(Model):
    """
    A data quality rule of a schema or a property.

    The type picks what the rule needs: a library rule needs a metric, a sql
    rule needs a query, and a custom rule needs an engine and an
    implementation. Library and sql rules compare their result with exactly
    one operator, such as mustBe. A text rule is only a description.

    The type is library by default, and a rule with a metric is a library
    rule.

    Examples:

        ```python
        Quality(metric="nullValues", mustBe=0)

        Quality(metric="rowCount", mustBeBetween=[100, 1000], dimension="completeness")

        Quality(
            type="sql",
            query="SELECT COUNT(*) FROM orders WHERE amount < 0",
            mustBe=0,
        )

        Quality(
            type="custom",
            engine="soda",
            implementation="duplicate_count(order_id) = 0",
        )

        Quality(type="text", description="Every order belongs to a known customer.")

        Property(name="email", quality=[Quality(metric="duplicateValues", mustBe=0)])
        ```
    """

    id: StableId | None = pyd.Field(
        None,
        description="Stable identifier, unique among the rules around it.",
    )
    name: str | None = pyd.Field(
        None,
        description="Short name of the rule.",
    )
    description: str | None = pyd.Field(
        None,
        description="What the rule checks.",
    )
    type: Literal["text", "library", "sql", "custom"] = pyd.Field(
        "library",
        description="Kind of rule: text, library, sql or custom.",
    )
    dimension: (
        Literal[
            "accuracy",
            "completeness",
            "conformity",
            "consistency",
            "coverage",
            "timeliness",
            "uniqueness",
        ]
        | None
    ) = pyd.Field(
        None,
        description="Data quality dimension the rule belongs to.",
    )
    method: str | None = pyd.Field(
        None,
        description="How the rule is checked.",
    )
    severity: str | None = pyd.Field(
        None,
        description="How serious a failure of the rule is.",
    )
    businessImpact: str | None = pyd.Field(
        None,
        description="What a failure of the rule means for the business.",
    )
    unit: str | None = pyd.Field(
        None,
        description="Unit of the result, such as rows or percent.",
    )
    schedule: str | None = pyd.Field(
        None,
        description="When the rule runs, in the syntax of the scheduler.",
    )
    scheduler: str | None = pyd.Field(
        None,
        description="Tool that runs the rule, such as cron.",
    )
    tags: list[str] | None = pyd.Field(
        None,
        description="Tags of the rule.",
    )
    customProperties: list[CustomProperty] | None = pyd.Field(
        None,
        description="Properties that the standard does not define.",
    )
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = pyd.Field(
        None,
        description="Links to sources with more details.",
    )
    metric: (
        Literal[
            "nullValues",
            "missingValues",
            "invalidValues",
            "duplicateValues",
            "rowCount",
        ]
        | None
    ) = pyd.Field(
        None,
        description="Metric a library rule measures.",
    )
    rule: str | None = pyd.Field(
        None,
        description="Deprecated name of the metric. Use metric.",
    )
    arguments: dict[str, Any] | None = pyd.Field(
        None,
        description="Extra arguments of the metric.",
    )
    query: str | None = pyd.Field(
        None,
        description="Query a sql rule runs.",
    )
    engine: str | None = pyd.Field(
        None,
        description="Engine a custom rule runs on, such as soda or greatExpectations.",
    )
    implementation: str | dict[str, Any] | None = pyd.Field(
        None,
        description="Rule in the language of the engine.",
    )
    mustBe: Any = pyd.Field(
        None,
        description="The result must be equal to this value.",
    )
    mustNotBe: Any = pyd.Field(
        None,
        description="The result must be different from this value.",
    )
    mustBeGreaterThan: int | float | None = pyd.Field(
        None,
        description="The result must be greater than this value.",
    )
    mustBeGreaterOrEqualTo: int | float | None = pyd.Field(
        None,
        description="The result must be greater than or equal to this value.",
    )
    mustBeLessThan: int | float | None = pyd.Field(
        None,
        description="The result must be less than this value.",
    )
    mustBeLessOrEqualTo: int | float | None = pyd.Field(
        None,
        description="The result must be less than or equal to this value.",
    )
    mustBeBetween: list[int | float] | None = pyd.Field(
        None,
        min_length=2,
        max_length=2,
        description="The result must be between these two values, smallest first.",
    )
    mustNotBeBetween: list[int | float] | None = pyd.Field(
        None,
        min_length=2,
        max_length=2,
        description="The result must not be between these two values, smallest first.",
    )

    @pyd.model_validator(mode="after")
    def has_what_its_type_needs(self) -> Self:
        """
        Raises SchemaError when the rule misses what its type needs.

        Examples:

            ```python
            Quality(type="sql", mustBe=0)
            # SchemaError: A sql quality rule needs a `query`

            Quality(metric="nullValues", mustBe=0, mustBeLessThan=10)
            # SchemaError: A library or sql quality rule needs exactly one operator, ...
            ```
        """
        declared_type = self.type if "type" in self.model_fields_set else None
        is_library = declared_type == "library" or self.metric is not None
        is_sql = declared_type == "sql"
        is_custom = declared_type == "custom"
        operators = [operator for operator in OPERATORS if operator in self.model_fields_set]

        SchemaError.raise_if(
            is_library and self.metric is None,
            "A library quality rule needs a `metric`",
        ).raise_if(
            is_sql and self.query is None,
            "A sql quality rule needs a `query`",
        ).raise_if(
            is_custom and (self.engine is None or self.implementation is None),
            "A custom quality rule needs an `engine` and an `implementation`",
        ).raise_if(
            (is_library or is_sql) and len(operators) != 1,
            "A library or sql quality rule needs exactly one operator, such as `mustBe`",
        )

        return self
