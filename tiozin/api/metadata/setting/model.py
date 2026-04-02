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

    # Identity
    kind: str = Field(config.default_setting_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Registry Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)


class JobRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_JOB_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    # Identity
    kind: str = Field(config.default_job_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Registry Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)


class SchemaRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_SCHEMA_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    # Identity
    kind: str = Field(config.default_schema_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Registry Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
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

    # Identity
    kind: str = Field(config.default_secret_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)


class TransactionRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_TRANSACTION_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    # Identity
    kind: str = Field(config.default_transaction_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)


class LineageRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_LINEAGE_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    # Identity
    kind: str = Field(config.default_lineage_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)
    # Lineage Properties
    emit_level: EmitLevel | None = Field(NULLABLE, description=docs.LINEAGE_REGISTRY_EMIT_LEVEL)


class MetricRegistryManifest(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIO_METRIC_REGISTRY_",
        extra="allow",
        str_strip_whitespace=True,
        env_ignore_empty=True,
    )

    # Identity
    kind: str = Field(config.default_metric_registry, description=docs.KIND)
    name: str | None = Field(NULLABLE, description=docs.REGISTRY_NAME)
    description: str | None = Field(NULLABLE, description=docs.REGISTRY_DESCRIPTION)
    # Properties
    location: str | None = Field(NULLABLE, description=docs.REGISTRY_LOCATION)
    timeout: int | None = Field(NULLABLE, description=docs.REGISTRY_TIMEOUT)
    readonly: bool | None = Field(NULLABLE, description=docs.REGISTRY_READONLY)
    cache: bool | None = Field(NULLABLE, description=docs.REGISTRY_CACHE)


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
    transaction: TransactionRegistryManifest = Field(default_factory=TransactionRegistryManifest)
    lineage: LineageRegistryManifest = Field(default_factory=LineageRegistryManifest)
    metric: MetricRegistryManifest = Field(default_factory=MetricRegistryManifest)


class SettingsManifest(Manifest):
    """
    Root manifest for a Tiozin settings file (tiozin.yaml).

    Declares application config, registry bindings, and default plugin values
    for a project or deployment environment.
    """

    kind: Literal["Settings"] = "Settings"
    registries: Registries = Field(default_factory=Registries)
