from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

from tiozin.exceptions import RequiredArgumentError

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
    - Raises SchemaNotFoundError when `failfast=True`, otherwise returns None.

    Uses configuration defined in SchemaRegistry.

    This is an internal detail. Use SchemaRegistry instead.
    """

    def get(self, subject: str, version: str = None) -> Schema:
        registry: SchemaRegistry = self.__wrapped__
        subject = self._resolve_subject(subject)
        version = version or registry.default_version

        registry.info(f"🔍 `{registry.context.name}` requested schema `{subject}`")

        try:
            schema = registry.get(subject)
            if not schema:
                raise SchemaNotFoundError(subject)
        except SchemaNotFoundError:
            if registry.failfast:
                raise
            registry.warning(f"Schema `{subject}` could not be found")
            return None

        if registry.show_schema:
            registry.info(f"Showing schema `{subject}`:\n{schema.to_yaml()}")

        return schema

    def register(self, subject: str, schema: Schema) -> None:
        registry: SchemaRegistry = self.__wrapped__
        subject = self._resolve_subject(subject)
        registry.info(f"📝 `{registry.context.name}` registering schema `{subject}`")
        registry.register(subject, schema)

    def _resolve_subject(self, subject: str) -> str:
        registry: SchemaRegistry = self.__wrapped__

        RequiredArgumentError.raise_if(
            not subject,
            "No schema subject identifier provided.",
        )

        if subject == "auto":
            subject = registry.subject_template

        return registry.context.render(subject)
