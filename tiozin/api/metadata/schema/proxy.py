import wrapt

from tiozin import config
from tiozin.exceptions import TiozinInternalError

from .exceptions import SchemaNotFoundError
from .model import Schema


class SchemaRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps a SchemaRegistry with subject resolution.

    Intercepts `get()` to render `identifier` with the active context variables,
    defaulting to `TIO_SCHEMA_SUBJECT_TEMPLATE` when `identifier` is not given.
    Defaults `version` to `TIO_SCHEMA_DEFAULT_VERSION` when not specified.

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

        subject = context.render(identifier or config.tiozin_schema_subject_template)
        version = version or config.tiozin_schema_default_version

        registry.info(f"🔍 `{context.name}` searching for schema subject `{subject}`")
        schema = registry.get(subject, version)

        SchemaNotFoundError.raise_if(
            schema is None,
            subject=subject,
        )

        TiozinInternalError.raise_if(
            not isinstance(schema, Schema),
            f"Schema registry returned unexpected object: `{type(schema)}`.",
        )

        if registry.show_schema:
            registry.info(f"Schema `{subject}`:\n{schema.to_yaml()}")

        return schema

    def try_get(self, identifier: str = None, version: str = None) -> Schema | None:
        try:
            return self.get(identifier, version)
        except SchemaNotFoundError as e:
            self.warning(e.message)
            return None
