from typing import Any, Self, TypeAlias

from tiozin import logs
from tiozin.api import EtlStep, Input, Job, JobManifest, Output, Runner, Tiozin, Transform
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.exceptions import TiozinInputError, TiozinInternalError
from tiozin.utils.helpers import trim

from ..reflection import try_get_public_setter
from .tiozin_registry import tiozin_registry

InputDefinition: TypeAlias = dict[str, Any] | InputManifest | Input
OutputDefinition: TypeAlias = dict[str, Any] | OutputManifest | Output
TransformDefinition: TypeAlias = dict[str, Any] | TransformManifest | Transform
RunnerDefinition: TypeAlias = dict[str, Any] | RunnerManifest | Runner


class JobBuilder:
    """
    Builds a Job through an explicit fluent interface.

    The builder accumulates declarative manifests or concrete Tiozin plugin instances
    and resolves everything only when build() is called.
    """

    def __init__(self) -> None:
        self._built = False
        self._logger = logs.get_logger(type(self).__name__)

        # Identity
        self._kind: str | None = None
        self._name: str | None = None
        self._description: str | None = None

        # Domain
        self._org: str | None = None
        self._region: str | None = None
        self._domain: str | None = None
        self._subdomain: str | None = None
        self._layer: str | None = None
        self._product: str | None = None
        self._model: str | None = None

        # Governance
        self._owner: str | None = None
        self._maintainer: str | None = None
        self._cost_center: str | None = None
        self._labels: dict[str, str] = {}

        # Runtime ETL
        self._runner: RunnerManifest | Runner | None = None
        self._inputs: list[InputManifest | Input] = []
        self._transforms: list[TransformManifest | Transform] = []
        self._outputs: list[OutputManifest | Output] = []

        # Job runtime options (provider-specific)
        self._options: dict[str, Any] = {}

    def with_kind(self, kind: str) -> Self:
        self._kind = trim(kind)
        return self

    def with_name(self, name: str) -> Self:
        self._name = trim(name)
        return self

    def with_description(self, description: str) -> Self:
        self._description = trim(description)
        return self

    def with_owner(self, owner: str) -> Self:
        self._owner = trim(owner)
        return self

    def with_maintainer(self, maintainer: str) -> Self:
        self._maintainer = maintainer
        return self

    def with_cost_center(self, cost_center: str) -> Self:
        self._cost_center = trim(cost_center)
        return self

    def with_label(self, key: str, value: str) -> Self:
        self._labels[key] = trim(value)
        return self

    def with_labels(self, labels: dict[str, str]) -> Self:
        self._labels.update(labels)
        return self

    def with_org(self, org: str) -> Self:
        self._org = trim(org)
        return self

    def with_region(self, region: str) -> Self:
        self._region = trim(region)
        return self

    def with_domain(self, domain: str) -> Self:
        self._domain = trim(domain)
        return self

    def with_subdomain(self, subdomain: str) -> Self:
        self._subdomain = trim(subdomain)
        return self

    def with_layer(self, layer: str) -> Self:
        self._layer = trim(layer)
        return self

    def with_product(self, product: str) -> Self:
        self._product = trim(product)
        return self

    def with_model(self, model: str) -> Self:
        self._model = trim(model)
        return self

    def with_runner(self, runner: RunnerDefinition) -> Self:
        match runner:
            case dict():
                self._runner = RunnerManifest.model_validate(runner)
            case Runner() | RunnerManifest():
                self._runner = runner
            case _:
                raise TiozinInputError(f"Invalid runner definition: {type(runner)}")

        return self

    def with_inputs(self, *values: InputDefinition) -> Self:
        for value in values:
            match value:
                case dict():
                    definition = InputManifest.model_validate(value)
                case Input() | InputManifest():
                    definition = value
                case _:
                    raise TiozinInputError(f"Invalid input definition: {type(value)}")
            self._inputs.append(definition)

        return self

    def with_transforms(self, *values: TransformDefinition) -> Self:
        for value in values:
            match value:
                case dict():
                    definition = TransformManifest.model_validate(value)
                case Transform() | TransformManifest():
                    definition = value
                case _:
                    raise TiozinInputError(f"Invalid transform definition: {type(value)}")
            self._transforms.append(definition)

        return self

    def with_outputs(self, *values: OutputDefinition) -> Self:
        for value in values:
            match value:
                case dict():
                    definition = OutputManifest.model_validate(value)
                case Output() | OutputManifest():
                    definition = value
                case _:
                    raise TiozinInputError(f"Invalid output definition: {type(value)}")
            self._outputs.append(definition)

        return self

    def with_field(self, field: str, value: Any) -> Self:
        setter = try_get_public_setter(self, f"with_{field}")

        if setter is not None:
            if isinstance(value, list):
                return setter(*value)
            return setter(value)

        self._options[field] = value
        return self

    def from_manifest(self, manifest: JobManifest) -> Self:
        for field in JobManifest.model_fields:
            self.with_field(field, getattr(manifest, field))

        self._options.update(manifest.model_extra)
        return self

    def _build_step(
        self, manifest: TransformManifest | OutputManifest | InputManifest | Tiozin
    ) -> EtlStep:
        manifest.org = manifest.org or self._org
        manifest.region = manifest.region or self._region
        manifest.domain = manifest.domain or self._domain
        manifest.subdomain = manifest.subdomain or self._subdomain
        manifest.layer = manifest.layer or self._layer
        manifest.product = manifest.product or self._product
        manifest.model = manifest.model or self._model
        return tiozin_registry.load_manifest(manifest)

    def build(self) -> Job:
        if self._built:
            raise TiozinInternalError("The builder can only be used once")

        job = tiozin_registry.safe_load(
            tiozin_role=Job,
            # identity
            kind=self._kind,
            name=self._name,
            description=self._description,
            # Governance
            owner=self._owner,
            maintainer=self._maintainer,
            cost_center=self._cost_center,
            labels=self._labels,
            # Domain
            org=self._org,
            region=self._region,
            domain=self._domain,
            subdomain=self._subdomain,
            layer=self._layer,
            product=self._product,
            model=self._model,
            # Pipeline
            runner=tiozin_registry.load_manifest(self._runner),
            inputs=[self._build_step(m) for m in self._inputs],
            transforms=[self._build_step(m) for m in self._transforms],
            outputs=[self._build_step(m) for m in self._outputs],
            **self._options,
        )

        if self._options:
            self._logger.warning(f"Unplanned job properties: {list(self._options.keys())}")

        self._built = True
        return job
