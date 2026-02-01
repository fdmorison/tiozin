from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from types import MappingProxyType as FrozenMapping
from typing import TYPE_CHECKING, Any, Self

import pendulum

from tiozin import env
from tiozin.exceptions import TiozinUnexpectedError
from tiozin.utils import RelativeDate, utcnow

if TYPE_CHECKING:
    from tiozin import Context


class TemplateContextBuilder:
    """
    Fluent builder for assembling template contexts.

    This builder centralizes how template variables are constructed and merged,
    providing a consistent and extensible way to expose:
    - relative dates
    - environment variables
    - user-defined variables
    - defaults
    - fields extracted from context objects (dataclasses)

    The final result is an immutable mapping designed to be safely consumed
    by template engines such as Jinja.
    """

    def __init__(self) -> None:
        self._defaults: dict[str, Any] = {}
        self._variables: dict[str, Any] = {}
        self._envvars: dict[str, str] = {}
        self._context: dict[str, Any] = {}
        self._datetime = None

    def with_relative_date(self, nominal_date: datetime = None) -> Self:
        """
        Sets the base datetime used for relative date computations.

        This datetime becomes the reference point for the `RelativeDate` object exposed in the
        template context as `DAY`.
        """
        if nominal_date and not isinstance(nominal_date, datetime):
            raise TypeError("nominal_date must be a datetime")

        self._datetime = pendulum.instance(nominal_date) if nominal_date else utcnow()
        return self

    def with_defaults(self, defaults: Mapping[str, object]) -> Self:
        """
        Adds default template variables.

        Defaults have the lowest precedence and are overridden by variables, context fields,
        relative dates, or environment variables defined later.
        """
        if not isinstance(defaults, Mapping):
            raise TypeError("defaults must be a mapping")

        self._defaults |= defaults
        return self

    def with_variables(self, variables: Mapping[str, object]) -> Self:
        """
        Adds explicit template variables.

        Variables added here override defaults but can still be overridden by context fields or
        other higher-precedence sources.
        """
        if not isinstance(variables, Mapping):
            raise TypeError("vars must be a mapping")

        self._variables |= variables
        return self

    def with_context(self, context: Context) -> Self:
        """
        Extracts template variables from a context object (dataclass).

        Only dataclass fields are considered. Fields marked with `metadata={"template": False}`
        are explicitly excluded.
        """
        if not is_dataclass(context):
            raise TypeError("context must be a dataclass instance")

        self._context |= {
            f.name: getattr(context, f.name)
            for f in fields(context)
            if f.metadata.get("template", True)
        }
        return self

    def with_envvars(self) -> Self:
        """
        Loads environment variables into the template context.

        This method reads `.env` files (recursively) and captures the resulting process environment.
        Both OS-level and `.env`-defined variables are included.

        The collected environment variables are exposed to templates under the `ENV` key.
        """
        env._env.read_env(recurse=True)
        self._envvars = dict(os.environ)
        return self

    def build(self) -> Mapping[str, object]:
        """
        Build template context with the following precedence (lowest → highest):

        - defaults
        - variables (user-provided)
        - context (system / dataclass-backed, authoritative)
        - ENV (isolated namespace)
        - RelativeDate flat fields (better DevExperience)
        - DAY (RelativeDate object)
        """
        result = {}
        result |= self._defaults
        result |= self._variables
        result |= self._context

        base_env = result.get("ENV") or {}

        TiozinUnexpectedError.raise_if(
            not isinstance(base_env, Mapping),
            f"ENV must be a mapping, got {base_env!r}",
        )

        result["ENV"] = {
            **base_env,
            **self._envvars,
        }

        if self._datetime:
            relative_date = RelativeDate(self._datetime)
            result |= relative_date.to_dict()
            result["DAY"] = relative_date

        return FrozenMapping(result)
