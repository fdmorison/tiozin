from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from types import MappingProxyType as FrozenMapping
from typing import Any, Self

import pendulum

from tiozin.utils.helpers import utcnow
from tiozin.utils.relative_date import RelativeDate


class TemplateContextBuilder:
    def __init__(self) -> None:
        self._defaults: dict[str, object] = {}
        self._variables: dict[str, object] = {}
        self._context: dict[str, object] = {}
        self._datetime = utcnow()

    def wiht_datetime(self, nominal_date: datetime) -> Self:
        if not isinstance(nominal_date, datetime):
            raise TypeError("nominal_date must be a datetime")

        self._datetime = pendulum.instance(nominal_date)
        return self

    def with_defaults(self, defaults: Mapping[str, object]) -> Self:
        if not isinstance(defaults, Mapping):
            raise TypeError("defaults must be a mapping")

        self._defaults |= defaults
        return self

    def with_variables(self, variables: Mapping[str, object]) -> Self:
        if not isinstance(variables, Mapping):
            raise TypeError("vars must be a mapping")

        self._variables |= variables
        return self

    def with_context(self, context: Any) -> Self:
        """
        Adds fields from a context object (dataclass) to the template context.

        Only fields with metadata {"template": True} are included.
        """
        if not is_dataclass(context):
            raise TypeError("context must be a dataclass instance")

        self._context |= {
            f.name: getattr(context, f.name)
            for f in fields(context)
            if f.metadata.get("template", True)
        }
        return self

    def build(self) -> Mapping[str, object]:
        date = RelativeDate(self._datetime)
        return FrozenMapping(
            {
                **self._defaults,
                **self._variables,
                **self._context,
                **date.to_dict(),
                "DAY": date,
            }
        )
