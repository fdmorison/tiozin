from typing import Literal, TypeAlias

from pydantic import BaseModel, Field

from tiozin import env

from .. import docs
from ..manifest import Manifest

STR: TypeAlias = str | None
BOOL: TypeAlias = bool | None
INT: TypeAlias = int | None


class SettingRegistryManifest(Manifest):
    # Identity
    kind: str = Field(env.TIO_SETTING_REGISTRY_KIND)
    name: STR = Field(None, description=docs.REGISTRY_NAME)
    description: STR = Field(None, description=docs.REGISTRY_DESCRIPTION)
    # Optional Commons
    location: STR = Field(env.TIO_SETTING_REGISTRY_LOCATION, description=docs.REGISTRY_LOCATION)
    timeout: INT = Field(env.TIO_SETTING_REGISTRY_TIMEOUT, description=docs.REGISTRY_TIMEOUT)
    readonly: BOOL = Field(env.TIO_SETTING_REGISTRY_READONLY, description=docs.REGISTRY_READONLY)
    cache: BOOL = Field(env.TIO_SETTING_REGISTRY_CACHE, description=docs.REGISTRY_CACHE)


class JobRegistryManifest(Manifest):
    # Identity
    kind: str = Field(env.TIO_JOB_REGISTRY_KIND)
    name: STR = Field(None, description=docs.REGISTRY_NAME)
    description: STR = Field(None, description=docs.REGISTRY_DESCRIPTION)
    # Optional Commons
    location: STR = Field(env.TIO_JOB_REGISTRY_LOCATION, description=docs.REGISTRY_LOCATION)
    timeout: INT = Field(env.TIO_JOB_REGISTRY_TIMEOUT, description=docs.REGISTRY_TIMEOUT)
    readonly: BOOL = Field(env.TIO_JOB_REGISTRY_READONLY, description=docs.REGISTRY_READONLY)
    cache: BOOL = Field(env.TIO_JOB_REGISTRY_CACHE, description=docs.REGISTRY_CACHE)


class SchemaRegistryManifest(Manifest):
    # Identity
    kind: str = Field(env.TIO_SCHEMA_REGISTRY_KIND)
    name: STR = Field(None, description=docs.REGISTRY_NAME)
    description: STR = Field(None, description=docs.REGISTRY_DESCRIPTION)
    # Optional Commons
    location: STR = Field(env.TIO_SCHEMA_REGISTRY_LOCATION, description=docs.REGISTRY_LOCATION)
    timeout: INT = Field(env.TIO_SCHEMA_REGISTRY_TIMEOUT, description=docs.REGISTRY_TIMEOUT)
    readonly: BOOL = Field(env.TIO_SCHEMA_REGISTRY_READONLY, description=docs.REGISTRY_READONLY)
    cache: BOOL = Field(env.TIO_SCHEMA_REGISTRY_CACHE, description=docs.REGISTRY_CACHE)


class SecretRegistryManifest(Manifest):
    # Identity
    kind: str = Field(env.TIO_SECRET_REGISTRY_KIND)
    name: STR = Field(None, description=docs.REGISTRY_NAME)
    description: STR = Field(None, description=docs.REGISTRY_DESCRIPTION)
    # Optional Commons
    location: STR = Field(env.TIO_SECRET_REGISTRY_LOCATION, description=docs.REGISTRY_LOCATION)
    timeout: INT = Field(env.TIO_SECRET_REGISTRY_TIMEOUT, description=docs.REGISTRY_TIMEOUT)
    readonly: BOOL = Field(env.TIO_SECRET_REGISTRY_READONLY, description=docs.REGISTRY_READONLY)
    cache: BOOL = Field(env.TIO_SECRET_REGISTRY_CACHE, description=docs.REGISTRY_CACHE)


class TransactionRegistryManifest(Manifest):
    # Identity
    kind: str = Field(env.TIO_TRANSACTION_REGISTRY_KIND)
    name: STR = Field(None, description=docs.REGISTRY_NAME)
    description: STR = Field(None, description=docs.REGISTRY_DESCRIPTION)
    # Optional Commons
    location: STR = Field(env.TIO_TRANSACTION_REGISTRY_LOCATION, description=docs.REGISTRY_LOCATION)
    timeout: INT = Field(env.TIO_TRANSACTION_REGISTRY_TIMEOUT, description=docs.REGISTRY_TIMEOUT)
    readonly: BOOL = Field(
        env.TIO_TRANSACTION_REGISTRY_READONLY, description=docs.REGISTRY_READONLY
    )
    cache: BOOL = Field(env.TIO_TRANSACTION_REGISTRY_CACHE, description=docs.REGISTRY_CACHE)


class LineageRegistryManifest(Manifest):
    # Identity
    kind: str = Field(env.TIO_LINEAGE_REGISTRY_KIND)
    name: STR = Field(None, description=docs.REGISTRY_NAME)
    description: STR = Field(None, description=docs.REGISTRY_DESCRIPTION)
    # Optional Commons
    location: STR = Field(env.TIO_LINEAGE_REGISTRY_LOCATION, description=docs.REGISTRY_LOCATION)
    timeout: INT = Field(env.TIO_LINEAGE_REGISTRY_TIMEOUT, description=docs.REGISTRY_TIMEOUT)
    readonly: BOOL = Field(env.TIO_LINEAGE_REGISTRY_READONLY, description=docs.REGISTRY_READONLY)
    cache: BOOL = Field(env.TIO_LINEAGE_REGISTRY_CACHE, description=docs.REGISTRY_CACHE)


class MetricRegistryManifest(Manifest):
    # Identity
    kind: str = Field(env.TIO_METRIC_REGISTRY_KIND)
    name: STR = Field(None, description=docs.REGISTRY_NAME)
    description: STR = Field(None, description=docs.REGISTRY_DESCRIPTION)
    # Optional Commons
    location: STR = Field(env.TIO_METRIC_REGISTRY_LOCATION, description=docs.REGISTRY_LOCATION)
    timeout: INT = Field(env.TIO_METRIC_REGISTRY_TIMEOUT, description=docs.REGISTRY_TIMEOUT)
    readonly: BOOL = Field(env.TIO_METRIC_REGISTRY_READONLY, description=docs.REGISTRY_READONLY)
    cache: BOOL = Field(env.TIO_METRIC_REGISTRY_CACHE, description=docs.REGISTRY_CACHE)


class Registries(BaseModel):
    """
    Bindings for each Tiozin registry.

    Each field maps to a registry. Absent fields fall back to the framework default.
    A None value for ``settings`` signals the end of settings delegation.
    """

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
