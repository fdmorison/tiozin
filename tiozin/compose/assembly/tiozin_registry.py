from __future__ import annotations

from collections import defaultdict
from typing import TypeVar

from tiozin.api import Tiozin
from tiozin.api.loggable import Loggable
from tiozin.api.metadata.model import Manifest
from tiozin.exceptions import (
    PluginConflictError,
    PluginNotFoundError,
    RequiredArgumentError,
    TiozinInputError,
)
from tiozin.utils.decorators import ensure_setup

from .. import reflection
from .tiozin_scanner import TiozinScanner

T = TypeVar("T", bound=Tiozin)


@ensure_setup
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
        self.ready = False

    def setup(self, *args, **kwargs) -> None:
        if self.ready:
            return

        self.info("Discovering Families...")
        families = TiozinScanner().scan()

        self.info("Summoning Tiozins to work...")
        for tiozins in families.values():
            for t in tiozins:
                self.register(t)

        self.ready = True

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

    def resolve(self, kind: str) -> type[Tiozin]:
        """
        Resolves a Tiozin class by kind without instantiating it.

        Args:
            kind: The Tiozin identifier.

        Raises:
            PluginNotFoundError: If no Tiozin matches the given kind.
            PluginConflictError: If multiple Tiozin plugins match without a unique identifier.

        Returns:
            The resolved Tiozin class.
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

        return next(iter(candidates))

    def load(self, kind: str, role: type[T] = None, **arguments) -> Tiozin:
        """
        Resolve and instantiate a Tiozin by kind. The `kind` may be:

        - Class name, e.g. "SparkFileInput"
        - Provider-qualified name, e.g. "tio_spark:SparkFileInput"
        - Python path, e.g. "my.module.SparkFileInput"

        If `role` is provided, the loaded class must be a subclass of it.

        Args:
            kind: Tiozin plugin class identifier.
            role: Tiozin plugin role class; the loaded plugin must satisfy it.
            **arguments: The Tiozin arguments

        Raises:
            PluginNotFoundError: If no Tiozin matches the given kind.
            PluginConflictError: If multiple Tiozin plugins match without a unique identifier.
            TiozinInputError: If the loaded plugin does not satisfy the given role.

        Returns:
            The new Tiozin instance.
        """
        tiozin = self.resolve(kind)

        TiozinInputError.raise_if(
            role and not issubclass(tiozin, role),
            "Tiozin '{name}' is not a '{role}'",
            name=tiozin.tiozin_name,
            role=role,
        )

        params = arguments.copy()
        params.pop("description", None)
        self.info(f"🧝 Tiozin `{tiozin.tiozin_name}` joined", **params)
        return tiozin(**arguments)

    def load_manifest(self, manifest: Manifest | Tiozin) -> Tiozin:
        """
        Loads a Tiozin from a manifest definition.
        """
        if isinstance(manifest, Tiozin):
            return manifest

        produces = getattr(type(manifest), "__produces__", None)
        role = produces() if produces is not None else None

        RequiredArgumentError.raise_if_missing(
            manifest=manifest,
            manifest_kind=manifest.kind,
            manifest_builds=role,
        )

        return self.load(
            kind=manifest.kind,
            role=role,
            **manifest.model_dump(exclude={"kind"}),
        )


tiozin_registry = TiozinRegistry()
