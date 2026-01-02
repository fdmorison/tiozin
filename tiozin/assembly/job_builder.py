import logging
from typing import Any, Self

from tiozin.api import Input, Job, JobManifest, Output, Runner, Transform
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.exceptions import InvalidInputError, TiozinUnexpectedError
from tiozin.utils.helpers import try_get_public_setter

from .plugin_factory import PluginFactory


class JobBuilder:
    """
    Builds a Job through an explicit fluent interface.

    The builder accumulates declarative manifests or concrete plugin instances
    and resolves everything only when build() is called.
    """

    def __init__(self) -> None:
        self._built = False
        self._logger = logging.getLogger(type(self).__name__)

        # identity
        self._kind: str | None = None
        self._name: str | None = None
        self._description: str | None = None
        self._owner: str | None = None
        self._maintainer: str | None = None
        self._cost_center: str | None = None
        self._labels: dict[str, str] = {}

        # taxonomy
        self._org: str | None = None
        self._region: str | None = None
        self._domain: str | None = None
        self._product: str | None = None
        self._model: str | None = None
        self._layer: str | None = None

        # pipeline
        self._runner: RunnerManifest | Runner | None = None
        self._inputs: list[InputManifest | Input] = []
        self._transforms: list[TransformManifest | Transform] = []
        self._outputs: list[OutputManifest | Output] = []

        # Job runtime options (provider-specific)
        self._options: dict[str, Any] = {}

    def kind(self, kind: str) -> Self:
        self._kind = kind
        return self

    def name(self, name: str) -> Self:
        self._name = name
        return self

    def description(self, description: str) -> Self:
        self._description = description
        return self

    def owner(self, owner: str) -> Self:
        self._owner = owner
        return self

    def maintainer(self, maintainer: str) -> Self:
        self._maintainer = maintainer
        return self

    def cost_center(self, cost_center: str) -> Self:
        self._cost_center = cost_center
        return self

    def label(self, key: str, value: str) -> Self:
        self._labels[key] = value
        return self

    def labels(self, labels: dict[str, str]) -> Self:
        self._labels.update(labels)
        return self

    def org(self, org: str) -> Self:
        self._org = org
        return self

    def region(self, region: str) -> Self:
        self._region = region
        return self

    def domain(self, domain: str) -> Self:
        self._domain = domain
        return self

    def product(self, product: str) -> Self:
        self._product = product
        return self

    def model(self, model: str) -> Self:
        self._model = model
        return self

    def layer(self, layer: str) -> Self:
        self._layer = layer
        return self

    def runner(self, runner: Runner | RunnerManifest | dict[str, Any]) -> Self:
        if isinstance(runner, (Runner, RunnerManifest)):
            self._runner = runner
        elif isinstance(runner, dict):
            self._runner = RunnerManifest.model_validate(runner)
        else:
            raise InvalidInputError(f"Invalid runner definition: {type(runner)}")

        return self

    def inputs(self, *values: Input | InputManifest | dict[str, Any]) -> Self:
        for value in values:
            match value:
                case Input() | InputManifest():
                    operator = value
                case dict():
                    operator = InputManifest.model_validate(value)
                case _:
                    raise InvalidInputError(f"Invalid input definition: {type(value)}")
            self._inputs.append(operator)

        return self

    def transforms(self, *values: Transform | TransformManifest | dict[str, Any]) -> Self:
        for value in values:
            match value:
                case Transform() | TransformManifest():
                    operator = value
                case dict():
                    operator = TransformManifest.model_validate(value)
                case _:
                    raise InvalidInputError(f"Invalid transform definition: {type(value)}")
            self._transforms.append(operator)

        return self

    def outputs(self, *values: Output | OutputManifest | dict[str, Any]) -> Self:
        for value in values:
            match value:
                case Output() | OutputManifest():
                    operator = value
                case dict():
                    operator = OutputManifest.model_validate(value)
                case _:
                    raise InvalidInputError(f"Invalid output definition: {type(value)}")
            self._outputs.append(operator)

        return self

    def set(self, field: str, value: Any) -> Self:
        setter = try_get_public_setter(self, field)

        if setter is not None:
            if isinstance(value, list):
                return setter(*value)
            return setter(value)

        self._options[field] = value
        return self

    def from_manifest(self, manifest: JobManifest) -> Self:
        for field in JobManifest.model_fields:
            self.set(field, getattr(manifest, field))

        self._options.update(manifest.model_extra)
        return self

    def build(self) -> Job:
        if self._built:
            raise TiozinUnexpectedError("The builder can only be used once")

        plugin_factory = PluginFactory()
        plugin_factory.setup()

        job = plugin_factory.load_job(
            # identity
            kind=self._kind,
            name=self._name,
            description=self._description,
            owner=self._owner,
            maintainer=self._maintainer,
            cost_center=self._cost_center,
            labels=self._labels,
            # taxonomy
            org=self._org,
            region=self._region,
            domain=self._domain,
            product=self._product,
            model=self._model,
            layer=self._layer,
            # pipeline
            runner=plugin_factory.load_manifest(self._runner),
            inputs=[plugin_factory.load_manifest(m) for m in self._inputs],
            transforms=[plugin_factory.load_manifest(m) for m in self._transforms],
            outputs=[plugin_factory.load_manifest(m) for m in self._outputs],
            **self._options,
        )

        if self._options:
            self._logger.warning(f"Unplanned job properties: {list(self._options.keys())}")

        self._built = True
        return job
