import wrapt

from tiozin import config
from tiozin.exceptions import TiozinInternalError

from .exceptions import SchemaNotFoundError
from .model import SchemaManifest

DEFAULT_SUBJECT_TEMPLATE = config.tiozin_schema_subject_template


class SchemaRegistryProxy(wrapt.ObjectProxy):
    f"""
    Internal proxy that wraps a SchemaRegistry with subject resolution.

    Intercepts `get()` to resolve the schema subject from either the provided `identifier` or the
    default template `{DEFAULT_SUBJECT_TEMPLATE}`, rendered with the active context variables (e.g.
    `acme.eu.sales.orders.raw.crm.order`). Defaults the version to `"latest"`when not specified.

    Raises `SchemaNotFoundError` when no schema is found, including when the registry returns
    `None`. Use `try_get()` on the registry to silently return `None` instead.

    This is an internal implementation detail. Callers rely on the `SchemaRegistry` interface and
    should not interact with this proxy directly.
    """

    def get(self, identifier: str = None, version: str = None) -> SchemaManifest:
        from .registry import SchemaRegistry

        registry: SchemaRegistry = self.__wrapped__
        context = registry.context

        subject = context.render(identifier or DEFAULT_SUBJECT_TEMPLATE)
        version = version or "latest"

        registry.info(f"🔍 `{context.name}` searching for schema subject `{subject}`")
        schema = registry.get(subject, version)

        SchemaNotFoundError.raise_if(
            schema is None,
            subject=subject,
        )

        TiozinInternalError.raise_if(
            not isinstance(schema, SchemaManifest),
            f"Schema registry returned unexpected object: `{type(schema)}`.",
        )

        if registry.show_schema:
            registry.info(f"Schema `{subject}`:\n{schema.to_yaml()}")

        return schema

    def try_get(self, identifier: str = None, version: str = None) -> SchemaManifest | None:
        try:
            return self.get(identifier, version)
        except SchemaNotFoundError as e:
            self.warning(e.message)
            return None
