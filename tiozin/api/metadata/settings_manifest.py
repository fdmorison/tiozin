from typing import Literal

from pydantic import BaseModel, Field

from tiozin import env

from .manifest import Manifest


class SettingsRegistryManifest(Manifest):
    kind: str = Field(env.TIO_SETTINGS_REGISTRY_KIND)


class JobRegistryManifest(Manifest):
    kind: str = Field(env.TIO_JOB_REGISTRY_KIND)


class SchemaRegistryManifest(Manifest):
    kind: str = Field(env.TIO_SCHEMA_REGISTRY_KIND)


class SecretRegistryManifest(Manifest):
    kind: str = Field(env.TIO_SECRET_REGISTRY_KIND)


class TransactionRegistryManifest(Manifest):
    kind: str = Field(env.TIO_TRANSACTION_REGISTRY_KIND)


class LineageRegistryManifest(Manifest):
    kind: str = Field(env.TIO_LINEAGE_REGISTRY_KIND)


class MetricRegistryManifest(Manifest):
    kind: str = Field(env.TIO_METRIC_REGISTRY_KIND)


class Registries(BaseModel):
    """
    Bindings for each Tiozin registry.

    Each field maps to a registry. Absent fields fall back to the framework default.
    """

    settings: SettingsRegistryManifest = Field(default_factory=SettingsRegistryManifest)
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
