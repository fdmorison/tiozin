from __future__ import annotations

from collections import defaultdict
from typing import TypeVar

from tiozin.api import Input, Job, Loggable, Output, Runner, Tiozin, Transform
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    JobManifest,
    Manifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.exceptions import (
    PluginConflictError,
    PluginNotFoundError,
    TiozinInputError,
)

from .. import reflection
from .tiozin_scanner import TiozinScanner

T = TypeVar("T", bound=Tiozin)

_MANIFEST_ROLE_MAP = {
    JobManifest: Job,
    RunnerManifest: Runner,
    InputManifest: Input,
    OutputManifest: Output,
    TransformManifest: Transform,
}


class TiozinRegistry(Loggable):
    """
    Discovers, registers, and resolves Tiozin plugins at runtime.

    On startup, scans each provider package to discover all Tiozin plugins (Jobs, Inputs, Outputs,
    Transforms, Runners, Registries) and indexes them by name, URI, tio path, and Python path.

    Discovery happens through entry points declared under the ``tiozin.family`` group. Each entry
    point represents a provider, not an individual Tiozin plugin. A provider is a Python package
    that groups related Tiozin plugins under a shared namespace.

    Example entry point configuration::

        [project.entry-points."tiozin.family"]
        tio_aws   = "tiozin.family.tio_aws"
        tio_spark = "tiozin.family.tio_spark"
        tio_john  = "mycompany.myteam.tio_john"

    Providers are encouraged to organize their Tiozin plugins in a familiar directory structure:

        ├── tio_john
        |   ├── jobs
        │   ├── inputs
        │   ├── outputs
        │   ├── registries
        │   ├── transforms
        │   └── runners

    Providers are affectionately called "Tios" (Portuguese for "uncles"), which is why their names
    must start with the ``tio_`` prefix. The ``tio_kernel`` provider is Tiozin's built-in provider
    and serves as both a baseline implementation and a reference for custom providers.

    When Tiozin plugins are registered, their names are qualified with the Family name, producing
    identifiers like ``tio_spark:SparkFileInput``. This qualification allows the registry to
    disambiguate when multiple providers expose Tiozin plugins with the same class name.
    """

    def __init__(self) -> None:
        super().__init__()
        self._index: dict[str, set[type[Tiozin]]] = defaultdict(set)
        self._tiozins: set[type[Tiozin]] = set()

        self.info("Discovering Families...")
        tios = TiozinScanner().scan()

        self.info("Summoning Tiozins to work...")
        for tiozins in tios.values():
            for tiozin in tiozins:
                self.register(tiozin)

    def register(self, tiozin: type[Tiozin]) -> None:
        """
        Registers a Tiozin class from a given Family (e.g. ``tio_pandas``, ``tio_spark``).
        """
        TiozinInputError.raise_if(
            not reflection.is_tiozin(tiozin),
            f"{tiozin} is not a Tiozin.",
        )

        if tiozin in self._tiozins:
            return

        self._index[tiozin.tiozin_name].add(tiozin)
        self._index[tiozin.tiozin_uri].add(tiozin)
        self._index[tiozin.tiozin_family_path].add(tiozin)
        self._index[tiozin.tiozin_python_path].add(tiozin)
        self._tiozins.add(tiozin)

    def load(self, kind: str, **args) -> Tiozin:
        """
        Resolves and loads a Tiozin by kind.

        The kind parameter accepts multiple formats: simple class names like
        ``"SparkFileInput"``, provider-qualified names like ``"tio_spark:SparkFileInput"``,
        or full Python paths like ``"my.module.SparkFileInput"``. Use qualified names
        to disambiguate when multiple providers expose Tiozin plugins with the same class name.

        Args:
            kind: The Tiozin identifier.
            **args: Arguments forwarded to the Tiozin constructor.

        Raises:
            PluginNotFoundError: If no Tiozin matches the given kind.
            AmbiguousPluginError: If multiple Tiozin plugins match without a unique identifier.

        Returns:
            A new instance of the resolved Tiozin.
        """
        candidates = self._index.get(kind)

        PluginNotFoundError.raise_if(
            not candidates,
            name=kind,
        )

        PluginConflictError.raise_if(
            len(candidates) > 1,
            name=kind,
            candidates=[p.tiozin_family_path for p in candidates],
        )

        tiozin = next(iter(candidates))
        params = args.copy()
        params.pop("description", None)
        self.info(f"🧝 Tiozin `{tiozin.tiozin_name}` joined with", **params)
        return tiozin(**args)

    def safe_load(self, kind: str, tiozin_role: type[T], **args) -> T:
        """
        Loads a Tiozin by kind and validates that it matches the expected type.
        """
        tiozin_instance: T = self.load(kind, **args)

        TiozinInputError.raise_if(
            not isinstance(tiozin_instance, tiozin_role),
            "Tiozin '{name}' is not a '{role}'",
            name=tiozin_instance.tiozin_name,
            role=tiozin_role,
        )

        return tiozin_instance

    def load_manifest(self, manifest: Manifest | Tiozin) -> Tiozin:
        """
        Loads a Tiozin from a manifest definition.
        """
        if isinstance(manifest, Tiozin):
            return manifest

        role = _MANIFEST_ROLE_MAP.get(type(manifest))

        TiozinInputError.raise_if(
            not role,
            f"No Tiozin can be load from manifest {type(manifest).__name__}",
        )

        tiozin_instance = self.safe_load(
            kind=manifest.kind,
            tiozin_role=role,
            **manifest.model_dump(exclude="kind"),
        )

        return tiozin_instance


tiozin_registry = TiozinRegistry()
