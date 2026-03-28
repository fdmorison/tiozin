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

        subject = identifier or DEFAULT_SUBJECT_TEMPLATE
        subject = context.render(subject)
        version = version or "latest"

        try:
            registry.info(f"🔍 `{context.name}` searching for schema subject `{subject}`")
            schema = registry.get(subject, version)
            if schema is None:
                raise SchemaNotFoundError(subject)
        except SchemaNotFoundError as e:
            registry.warning(e.message)
            raise

        TiozinInternalError.raise_if(
            not isinstance(schema, SchemaManifest),
            f"Schema registry returned unexpected object for `{subject}`: `{type(schema)}`.",
        )

        if registry.show_schema:
            registry.info(f"Schema `{subject}`:\n{schema.to_yaml()}")

        return schema
