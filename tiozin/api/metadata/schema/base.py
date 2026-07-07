from abc import abstractmethod

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
    Schema registry interface.

    Provides a storage-agnostic contract for retrieving and storing schemas
    (e.g., Confluent Schema Registry).

    Configuration (priority order):
    1. tiozin.yaml (recommended)
    2. Environment variables: TIO_SCHEMA_REGISTRY_*
    3. Direct instantiation (not recommended)

    Environment variables are resolved into default configuration values
    (e.g., subject_template, default_version) via `config`.

    Attributes:
        show_schema: If True, logs schemas after `get()`.
        subject_template: Template to resolve subject when not provided.
        default_version: Default schema version (e.g., "latest").

    Example (tiozin.yaml):
        schema:
            kind: FileSchemaRegistry
            location: examples/schemas
            timeout: 5
            readonly: false
            cache: false
            subject_template: "{{domain}}.{{layer}}.{{product}}.{{model}}"
            default_version: latest
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

    @abstractmethod
    def get(self, subject: str, version: str = None) -> Schema:
        """
        Retrieve a schema by identifier.

        Raises:
            NotFoundException: When not found and `failfast=True`.
        """

    @abstractmethod
    def register(self, subject: str, value: Schema) -> None:
        """Register a schema in the registry."""
