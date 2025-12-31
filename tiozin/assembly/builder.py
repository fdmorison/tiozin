import logging
from typing import Any, Self

from tiozin.api import Input, Job, JobManifest, Output, Runner, Transform
from tiozin.exceptions import InvalidInputError, TiozinUnexpectedError

from .plugin_factory import PluginFactory


class JobBuilder:
    """
    Builds a Job through an explicit fluent interface.

    The builder accumulates declarative manifests or concrete plugin instances
    and resolves everything only when build() is called.
    """

    def __init__(self) -> None:
        self._built = False
        self._plugin_factory = PluginFactory()
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
        self._runner: dict | Runner | None = None
        self._inputs: list[dict | Input] = []
        self._transforms: list[dict | Transform] = []
        self._outputs: list[dict | Output] = []

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

    def runner(self, runner: Runner | dict[str, Any]) -> Self:
        if isinstance(runner, Runner):
            self._runner = runner
        elif isinstance(runner, dict):
            self._runner = runner
        else:
            raise InvalidInputError(f"Invalid runner definition: {type(runner)}")

        return self

    def inputs(self, *values: Input | dict[str, Any]) -> Self:
        for value in values:
            if isinstance(value, Input):
                operator = value
            elif isinstance(value, dict):
                operator = value
            else:
                raise InvalidInputError(f"Invalid input definition: {type(value)}")
            self._inputs.append(operator)

        return self

    def transforms(self, *values: Transform | dict[str, Any]) -> Self:
        for value in values:
            if isinstance(value, Transform):
                operator = value
            elif isinstance(value, dict):
                operator = value
            else:
                raise InvalidInputError(f"Invalid transform definition: {type(value)}")
            self._transforms.append(operator)

        return self

    def outputs(self, *values: Output | dict[str, Any]) -> Self:
        for value in values:
            if isinstance(value, Output):
                operator = value
            elif isinstance(value, dict):
                operator = value
            else:
                raise InvalidInputError(f"Invalid output definition: {type(value)}")
            self._outputs.append(operator)

        return self

    def set(self, field: str, value: Any) -> Self:
        setter = getattr(self, field, None)
        if callable(setter) and not field.startswith("_"):
            if value is not None:
                setter(value)
        else:
            raise InvalidInputError(f"Field `{field}` is not a valid builder attribute.")
        return self

    def from_manifest(self, manifest: JobManifest) -> Self:
        for field in JobManifest.model_fields:
            if field not in ("runner", "inputs", "transforms", "outputs"):
                self.set(field, getattr(manifest, field))

        self.runner(
            manifest.runner.model_dump(),
        )

        self.inputs(
            *[
                {"name": field, **operator.model_dump()}
                for field, operator in manifest.inputs.items()
            ]
        )
        self.transforms(
            *[
                {"name": field, **operator.model_dump()}
                for field, operator in manifest.transforms.items()
            ]
        )
        self.outputs(
            *[
                {"name": field, **operator.model_dump()}
                for field, operator in manifest.outputs.items()
            ]
        )
        return self

    def build(self) -> Job:
        if self._built:
            raise TiozinUnexpectedError("The builder can only be used once")

        self._plugin_factory.setup()

        runner = (
            self._plugin_factory.get_runner(**self._runner)
            if isinstance(self._runner, dict)
            else self._runner
        )

        inputs = [
            self._plugin_factory.get_input(**operator) if isinstance(operator, dict) else operator
            for operator in self._inputs
        ]

        transforms = [
            self._plugin_factory.get_transform(**operator)
            if isinstance(operator, dict)
            else operator
            for operator in self._transforms
        ]

        outputs = [
            self._plugin_factory.get_output(**operator) if isinstance(operator, dict) else operator
            for operator in self._outputs
        ]

        job = self._plugin_factory.get_job(
            kind=self._kind,
            name=self._name,
            description=self._description,
            owner=self._owner,
            maintainer=self._maintainer,
            cost_center=self._cost_center,
            labels=self._labels,
            org=self._org,
            region=self._region,
            domain=self._domain,
            product=self._product,
            model=self._model,
            layer=self._layer,
            runner=runner,
            inputs=inputs,
            transforms=transforms,
            outputs=outputs,
        )

        self._built = True
        return job
