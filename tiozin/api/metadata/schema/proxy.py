from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

from tiozin.exceptions import RequiredArgumentError, TiozinInternalError

from .exceptions import SchemaNotFoundError
from .model import Schema

if TYPE_CHECKING:
    from .registry import SchemaRegistry


class SchemaRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps SchemaRegistry with Tiozin behavior.

    Resolves `identifier` into a schema subject using the active context.
    Supports plain strings or templates (e.g., "{{domain}}.{{product}}.{{model}}").

    Adds:
    - `auto` subject (renders registry.subject_template)
    - Default version when not provided
    - Raises SchemaNotFoundError if result is None
    - Raises TiozinInternalError if result is not a valid schema

    Uses configuration defined in SchemaRegistry.

    This is an internal detail. Use SchemaRegistry instead.
    """

    @property
    def _registry(self) -> SchemaRegistry:
        return self.__wrapped__

    def get(self, subject: str, version: str = None) -> Schema:
        registry = self._registry
        subject = self._resolve_subject(subject)
        version = version or self._registry.default_version

        registry.info(f"🔍 `{registry.context.name}` requested schema subject `{subject}`")
        schema = registry.get(subject, version)

        if not schema:
            SchemaNotFoundError.raise_if(registry.failfast, subject)
            return None

        TiozinInternalError.raise_if(
            registry.failfast and not isinstance(schema, Schema),
            f"Schema registry returned unexpected object for `{subject}`: {type(schema)}.",
        )

        if registry.show_schema:
            registry.info(f"Schema `{subject}`:\n{schema.to_yaml()}")

        return schema

    def register(self, subject: str, schema: Schema) -> None:
        registry = self._registry
        subject = self._resolve_subject(subject)
        registry.info(f"📝 `{registry.context.name}` registering schema subject `{subject}`")
        registry.register(subject, schema)

    def _resolve_subject(self, subject: str) -> str:
        RequiredArgumentError.raise_if(
            not subject,
            "No schema subject identifier provided.",
        )

        if subject == "auto":
            subject = self._registry.subject_template

        return self._registry.context.render(subject)
