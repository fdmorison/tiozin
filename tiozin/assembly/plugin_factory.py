from __future__ import annotations

from collections import defaultdict
from typing import TypeVar

from tiozin.api import Loggable, PlugIn
from tiozin.api.metadata.job_manifest import Manifest
from tiozin.exceptions import (
    AmbiguousPluginError,
    InvalidInputError,
    PluginKindError,
    PluginNotFoundError,
)
from tiozin.utils import reflection

from .plugin_scanner import PluginScanner

T = TypeVar("T", bound=PlugIn)


class PluginRegistry(Loggable):
    """
    The PluginFactory loads each provider package and scans it to automatically discover
    all plugin classes defined inside it, such as Inputs, Outputs, Transforms, Runners,
    and Registries.

    Plugin discovery in Tiozin happens through entry points declared under the
    `tiozin.family` group. Each entry point represents a provider — not an individual
    plugin. A provider is simply a Python package that groups related plugins under a
    shared namespace.

    For example, the following entry point configuration:

        [project.entry-points."tiozin.family"]
        tio_aws   = "tiozin.family.tio_aws"
        tio_spark = "tiozin.family.tio_spark"
        tio_john  = "mycompany.myteam.tio_john"

    declares three providers. While `tio_aws` and `tio_spark` may live under the built-in
    `tiozin.family` namespace, `tio_john` comes from an external package owned by a
    different team. From Tiozin's point of view, all of them are treated exactly the same.

    Although not required, providers are encouraged to organize their plugins using a
    simple and familiar directory structure, for example:

        ├── tio_john
        |   ├── jobs
        │   ├── inputs
        │   ├── outputs
        │   ├── registries
        │   ├── transforms
        │   └── runners

    In Tiozin, providers are affectionately called "Tios" (Portuguese for "uncles"),
    which is why provider names must start with the `tio_` prefix. The `tio_kernel`
    provider is Tiozin's built-in provider and serves both as a baseline implementation
    and as a reference example for custom providers.

    When plugins are registered, their names are qualified with the provider name,
    resulting in identifiers like `tio_spark:SparkFileInput`. This qualification becomes
    important when multiple providers expose plugins with the same class name, as it
    allows Tiozin to disambiguate and resolve the correct plugin.
    """

    def __init__(self) -> None:
        super().__init__()
        self._index: dict[str, set[type[PlugIn]]] = defaultdict(set)
        self._plugins: set[type[PlugIn]] = set()

        self.info("Waking up the Tios and Tias...")
        tios = PluginScanner().scan()

        self.info("Summoning Tiozins to work...")
        for plugins in tios.values():
            for plugin in plugins:
                self.register(plugin)

    def register(self, plugin: type[PlugIn]) -> None:
        """
        Register a new plugin from a given provider namespace (e.g. `tio_pandas`, `tio_spark`)
        """
        InvalidInputError.raise_if(
            not reflection.is_plugin(plugin),
            f"{plugin} is not a Plugin.",
        )

        if plugin in self._plugins:
            return

        metadata = plugin.__tiometa__
        self._index[metadata.name].add(plugin)
        self._index[metadata.uri].add(plugin)
        self._index[metadata.tio_path].add(plugin)
        self._index[metadata.python_path].add(plugin)
        self._plugins.add(plugin)

    def load(self, kind: str, **args) -> PlugIn:
        """
        Resolve and loads a plugin by kind.

        The kind parameter accepts multiple formats for flexibility: simple class names
        like "MyPlugin", provider-qualified names like "tio_pandas:MyPlugin", or full
        Python paths like "my.module.MyPlugin". Use provider-qualified or Python paths to
        disambiguate when multiple plugins share the same class name.

        Args:
            kind: The Plugin identifier.
            **args: Plugin arguments to be injected in the plugin constructor.

        Raises:
            PluginNotFoundError: If the plugin does not exist or does not match the requested role.
            AmbiguousPluginError: If multiple plugins match the kind without a unique identifier.

        Returns:
            A new instance of the resolved plugin.
        """
        candidates = self._index.get(kind)

        PluginNotFoundError.raise_if(
            not candidates,
            plugin_name=kind,
        )

        AmbiguousPluginError.raise_if(
            len(candidates) > 1,
            plugin_name=kind,
            candidates=[p.__tiometa__.tio_path for p in candidates],
        )

        plugin = next(iter(candidates))
        params = args.copy()
        params.pop("description", None)
        self.info("🧝 Tiozin joined the pipeline", kind=kind, **params)
        return plugin(**args)

    def safe_load(self, kind: str, plugin_kind: type[T], **args) -> T:
        """
        Instantiates one plugin from kind and arguments, then checks types.
        """
        plugin: T = self.load(kind, **args)

        PluginKindError.raise_if(
            not isinstance(plugin, plugin_kind),
            plugin_name=plugin.plugin_name,
            plugin_kind=plugin_kind,
        )

        return plugin

    def load_manifest(self, manifest: Manifest | PlugIn) -> PlugIn:
        """
        Instantiates one plugin from a manifest definition.
        """
        if isinstance(manifest, PlugIn):
            return manifest

        PluginKindError.raise_if(
            not manifest.for_kind(),
            f"Unsupported manifest {type(manifest).__name__} does not specify a Plugin Kind",
        )

        plugin = self.safe_load(
            kind=manifest.kind,
            plugin_kind=manifest.for_kind(),
            **manifest.model_dump(exclude="kind"),
        )

        return plugin


plugin_registry = PluginRegistry()
