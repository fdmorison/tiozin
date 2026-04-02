import wrapt

from tiozin.exceptions import RequiredArgumentError, TiozinInternalError

from .exceptions import SchemaNotFoundError
from .model import Schema


class SchemaRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps a SchemaRegistry with subject resolution.

    Intercepts `get()` to render `identifier` with the active context variables,
    defaulting to `TIO_SCHEMA_REGISTRY_SUBJECT_TEMPLATE` when `identifier` is not given.
    Defaults `version` to `TIO_SCHEMA_REGISTRY_DEFAULT_VERSION` when not specified.

    Raises `SchemaNotFoundError` when no schema is found, including when the
    registry returns `None`. Use `try_get()` on the registry to silently return
    `None` instead.

    This is an internal implementation detail. Callers rely on the
    `SchemaRegistry` interface and should not interact with this proxy directly.
    """

    def get(self, identifier: str = None, version: str = None) -> Schema:
        from .registry import SchemaRegistry

        registry: SchemaRegistry = self.__wrapped__
        context = registry.context
        subject = identifier or registry.subject_template
        version = version or registry.default_version

        RequiredArgumentError.raise_if(
            not subject,
            "No schema subject identifier provided.",
        )

        subject = context.render(subject)
        registry.info(f"🔍 `{context.name}` searching for schema subject `{subject}`")
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
