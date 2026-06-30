from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from tiozin import config

from .. import docs
from ..lineage.enums import EmitLevel
from ..model import Manifest

NULLABLE = None


class SettingRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_SETTING_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    @classmethod
    def __produces__(cls):
        from .registry import SettingRegistry

        return SettingRegistry

    # Identity
    kind: str = Field(config.default_setting_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Registry Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    failfast: bool | None = Field(NULLABLE, description=docs.REGISTRY_FAILFAST)


class JobRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_JOB_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    @classmethod
    def __produces__(cls):
        from ..job.registry import JobRegistry

        return JobRegistry

    # Identity
    kind: str = Field(config.default_job_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Registry Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    failfast: bool | None = Field(NULLABLE, description=docs.REGISTRY_FAILFAST)


class SchemaRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_SCHEMA_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    @classmethod
    def __produces__(cls):
        from ..schema.registry import SchemaRegistry

        return SchemaRegistry

    # Identity
    kind: str = Field(config.default_schema_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Registry Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    failfast: bool | None = Field(NULLABLE, description=docs.REGISTRY_FAILFAST)
    # Schema Registry Properties
    show_schema: bool | None = Field(NULLABLE, description=docs.SCHEMA_REGISTRY_SHOW_SCHEMA)
    subject_template: str | None = Field(
        NULLABLE, description=docs.SCHEMA_REGISTRY_SUBJECT_TEMPLATE
    )
    default_version: str | None = Field(NULLABLE, description=docs.SCHEMA_REGISTRY_DEFAULT_VERSION)


class SecretRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_SECRET_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    @classmethod
    def __produces__(cls):
        from ..secret.registry import SecretRegistry

        return SecretRegistry

    # Identity
    kind: str = Field(config.default_secret_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    failfast: bool | None = Field(NULLABLE, description=docs.REGISTRY_FAILFAST)


class BatchRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_BATCH_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    @classmethod
    def __produces__(cls):
        from ..batch.registry import BatchRegistry

        return BatchRegistry

    # Identity
    kind: str = Field(config.default_batch_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    failfast: bool | None = Field(NULLABLE, description=docs.REGISTRY_FAILFAST)
    # Batch Properties
    retries: int | None = Field(NULLABLE, description=docs.BATCH_REGISTRY_RETRIES)


class LineageRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_LINEAGE_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    @classmethod
    def __produces__(cls):
        from ..lineage.registry import LineageRegistry

        return LineageRegistry

    # Identity
    kind: str = Field(config.default_lineage_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    failfast: bool | None = Field(NULLABLE, description=docs.REGISTRY_FAILFAST)
    # Lineage Properties
    emit_level: EmitLevel | None = Field(NULLABLE, description=docs.LINEAGE_REGISTRY_EMIT_LEVEL)


class MetricRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_METRIC_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    @classmethod
    def __produces__(cls):
        from ..metric.registry import MetricRegistry

        return MetricRegistry

    # Identity
    kind: str = Field(config.default_metric_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    failfast: bool | None = Field(NULLABLE, description=docs.REGISTRY_FAILFAST)


class Registries(BaseSettings):
    """
    Bindings for each Tiozin registry.

    Each field maps to a registry. Absent fields fall back to the framework default.
    A None value for ``settings`` signals the end of settings delegation.
    """

    model_config = SettingsConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    setting: SettingRegistryManifest | None = None
    job: JobRegistryManifest = Field(default_factory=JobRegistryManifest)
    schema: SchemaRegistryManifest = Field(default_factory=SchemaRegistryManifest)
    secret: SecretRegistryManifest = Field(default_factory=SecretRegistryManifest)
    batch: BatchRegistryManifest = Field(default_factory=BatchRegistryManifest)
    lineage: LineageRegistryManifest = Field(default_factory=LineageRegistryManifest)
    metric: MetricRegistryManifest = Field(default_factory=MetricRegistryManifest)


class RuntimeDefault(BaseSettings):
    """
    Default argument values for a specific plugin kind.

    Applied by TiozinRegistry when loading the matching plugin, filling in
    arguments not provided at the call site.
    """

    model_config = SettingsConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    kind: str


class SettingsManifest(Manifest):
    """
    Root manifest for a Tiozin settings file (tiozin.yaml).

    Declares application config, registry bindings, and default plugin values
    for a project or deployment environment.
    """

    kind: Literal["Settings"] = "Settings"
    registries: Registries = Field(default_factory=Registries)
    runtime_defaults: list[RuntimeDefault] = Field(default_factory=list)
