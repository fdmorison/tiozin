from __future__ import annotations

from collections import defaultdict
from typing import TypeVar

from tiozin.api import Loggable, Tiozin
from tiozin.api.metadata.job_manifest import Manifest
from tiozin.exceptions import (
    AmbiguousPluginError,
    InvalidInputError,
    PluginKindError,
    PluginNotFoundError,
)

from .. import reflection
from .tiozin_scanner import TiozinScanner

T = TypeVar("T", bound=Tiozin)


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

    When Tiozin plugins are registered, their names are qualified with the Tio name, producing
    identifiers like ``tio_spark:SparkFileInput``. This qualification allows the registry to
    disambiguate when multiple providers expose Tiozin plugins with the same class name.
    """

    def __init__(self) -> None:
        super().__init__()
        self._index: dict[str, set[type[Tiozin]]] = defaultdict(set)
        self._tiozins: set[type[Tiozin]] = set()

        self.info("Waking up the Tios and Tias...")
        tios = TiozinScanner().scan()

        self.info("Summoning Tiozins to work...")
        for tiozins in tios.values():
            for tiozin in tiozins:
                self.register(tiozin)

    def register(self, tiozin: type[Tiozin]) -> None:
        """
        Registers a Tiozin class from a given provider (e.g. ``tio_pandas``, ``tio_spark``).
        """
        InvalidInputError.raise_if(
            not reflection.is_tiozin(tiozin),
            f"{tiozin} is not a Tiozin.",
        )

        if tiozin in self._tiozins:
            return

        self._index[tiozin.tiozin_name].add(tiozin)
        self._index[tiozin.tiozin_uri].add(tiozin)
        self._index[tiozin.tiozin_tio_path].add(tiozin)
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
            tiozin_name=kind,
        )

        AmbiguousPluginError.raise_if(
            len(candidates) > 1,
            tiozin_name=kind,
            candidates=[p.tiozin_tio_path for p in candidates],
        )

        tiozin = next(iter(candidates))
        params = args.copy()
        params.pop("description", None)
        self.info("🧝 Tiozin joined the pipeline", kind=kind, **params)
        return tiozin(**args)

    def safe_load(self, kind: str, tiozin_kind: type[T], **args) -> T:
        """
        Loads a Tiozin by kind and validates that it matches the expected type.
        """
        tiozin_instance: T = self.load(kind, **args)

        PluginKindError.raise_if(
            not isinstance(tiozin_instance, tiozin_kind),
            tiozin_name=tiozin_instance.tiozin_name,
            tiozin_kind=tiozin_kind,
        )

        return tiozin_instance

    def load_manifest(self, manifest: Manifest | Tiozin) -> Tiozin:
        """
        Loads a Tiozin from a manifest definition.
        """
        if isinstance(manifest, Tiozin):
            return manifest

        PluginKindError.raise_if(
            not manifest.for_kind(),
            f"Unsupported manifest {type(manifest).__name__} does not specify a Tiozin Kind",
        )

        tiozin_instance = self.safe_load(
            kind=manifest.kind,
            tiozin_kind=manifest.for_kind(),
            **manifest.model_dump(exclude="kind"),
        )

        return tiozin_instance


tiozin_registry = TiozinRegistry()
