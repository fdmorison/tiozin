from typing import TYPE_CHECKING

import wrapt

from tiozin.exceptions import RequiredArgumentError, TiozinInternalError

from .exceptions import SchemaNotFoundError
from .model import Schema

if TYPE_CHECKING:
    from .registry import SchemaRegistry


class SchemaRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps a SchemaRegistry to add Tiozin's core behavior.

    It resolves the `identifier` into a schema subject using the active context.
    The identifier can be a plain string or a template like `{{domain}}.{{product}}.{{model}}`.

    The proxy adds:

    - The `auto` subject, which renders the default subject template.
    - The default version when `version` is not provided.
    - Raises `SchemaNotFoundError` when the registry returns `None`.
    - Raises `TiozinInternalError` when the registry returns a non-schema object.

    These defaults come from `tiozin.yaml` or from the environment variables
    `TIO_SCHEMA_REGISTRY_SUBJECT_TEMPLATE` and `TIO_SCHEMA_REGISTRY_DEFAULT_VERSION`. Example:

    ```yaml
    schema:
        kind: FileSchemaRegistry
        ...
        subject_template: "{{domain}}.{{layer}}.{{product}}.{{model}}"
        default_version: latest
    ```

    ```bash
    export TIO_SCHEMA_REGISTRY_SUBJECT_TEMPLATE="{{domain}}.{{layer}}.{{product}}.{{model}}"
    export TIO_SCHEMA_REGISTRY_DEFAULT_VERSION="latest"
    ```

    This is an internal implementation detail. Callers should use the
    SchemaRegistry interface instead of interacting with this proxy directly.
    """

    def get(self, identifier: str, version: str = None) -> Schema:
        registry: SchemaRegistry = self.__wrapped__

        subject = self._resolve_subject(identifier)
        version = version or registry.default_version

        registry.info(f"🔍 `{registry.context.name}` searching for schema subject `{subject}`")
        schema = registry.get(subject, version)

        SchemaNotFoundError.raise_if(
            schema is None,
            subject=subject,
        )

        TiozinInternalError.raise_if(
            not isinstance(schema, Schema),
            f"Schema registry returned unexpected object for `{subject}`: {type(schema)}.",
        )

        if registry.show_schema:
            registry.info(f"Schema `{subject}`:\n{schema.to_yaml()}")

        return schema

    def register(self, identifier: str, schema: Schema) -> None:
        registry: SchemaRegistry = self.__wrapped__
        subject = self._resolve_subject(identifier)
        registry.info(f"📝 `{registry.context.name}` registering schema subject `{subject}`")
        registry.register(subject, schema)

    def _resolve_subject(self, identifier: str) -> str:
        registry: SchemaRegistry = self.__wrapped__

        RequiredArgumentError.raise_if(
            not identifier,
            "No schema subject identifier provided.",
        )

        if identifier == "auto":
            identifier = registry.subject_template

        return registry.context.render(identifier)
