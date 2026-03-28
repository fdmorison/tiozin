import wrapt

from tiozin import config

from ..registry import Registry
from .exceptions import SchemaNotFoundError
from .model import SchemaManifest

DEFAULT_SUBJECT_TEMPLATE = config.tiozin_schema_subject_template


class SchemaRegistryProxy(wrapt.ObjectProxy):
    """
    Internal proxy that wraps a SchemaRegistry with subject resolution and
    graceful fallback behavior.

    Intercepts `get()` to resolve the schema subject from either the provided
    `identifier` or a configured template rendered with the current context.
    Defaults the version to `"latest"` when not specified.

    Logs retrieval attempts and, when the schema is not found, emits a warning
    and returns `None` instead of propagating the error.

    This is an internal implementation detail. Callers rely on the
    `SchemaRegistry` interface and should not interact with this proxy directly.
    """

    def get(self, identifier: str = None, version: str = None) -> SchemaManifest:
        registry: Registry = self.__wrapped__

        subject = identifier or DEFAULT_SUBJECT_TEMPLATE
        subject = registry.context.render(subject)
        version = version or "latest"

        try:
            registry.info(f"Downloading schema `{subject}`")
            return registry.get(subject, version)
        except SchemaNotFoundError:
            registry.warning(f"Schema `{subject}` was not found.")

        return None
