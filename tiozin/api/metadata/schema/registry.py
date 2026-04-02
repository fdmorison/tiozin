from tiozin import config
from tiozin.compose import tioproxy
from tiozin.compose.templating.template_string import TemplateString
from tiozin.utils import default

from ..registry import Registry
from .model import Schema
from .proxy import SchemaRegistryProxy


@tioproxy(SchemaRegistryProxy)
class SchemaRegistry(Registry[Schema]):
    """
    Retrieves and stores schemas.

    Storage-agnostic contract for schema backends (e.g., Confluent Schema Registry).
    Available in Context for schema handling in Transforms, Inputs, and Outputs.

    This service can be configured via:

    1. tiozin.yaml (recommended)
    2. Environment variables prefixed with `TIO_SCHEMA_REGISTRY_*`
    3. Direct instantiation via constructor (not recommended)

    Configuration is resolved from tiozin.yaml when available, falling back to
    environment variables. Check tiozin/api/metadata/setting/model.py for details.

    Attributes:
        show_schema:
            When `True`, logs the retrieved schema after each successful `get()`.
            Can be configured via `TIO_SCHEMA_REGISTRY_SHOW_SCHEMA`.

        subject_template:
            Jinja template used to resolve the schema subject when none is provided.
            Can be configured via `TIO_SCHEMA_REGISTRY_SUBJECT_TEMPLATE`.

        default_version:
            Schema version used when none is specified (e.g., "latest").
            Can be configured via `TIO_SCHEMA_REGISTRY_DEFAULT_VERSION`.

    Example in tiozin.yaml:

        schema:
            kind: FileSchemaRegistry
            description: File-based schema registry for local development
            location: examples/schemas
            timeout: 5
            readonly: false
            cache: false
            subject_template: "{{domain}}.{{layer}}.{{product}}.{{model}}"
            default_version: latest
            custom_property: 12345
    """

    def __init__(
        self,
        show_schema: bool = None,
        subject_template: str = None,
        default_version: str = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.show_schema = default(show_schema, config.default_schema_show_schema)
        self.subject_template = TemplateString(
            subject_template or config.default_schema_subject_template
        )
        self.default_version = default(default_version, config.default_schema_default_version)
