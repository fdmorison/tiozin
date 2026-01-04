from typing import TypeVar

from tiozin.api import Input, Job, Output, PlugIn, Resource, Runner, Transform
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    Manifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.exceptions import AmbiguousPluginError, PluginNotFoundError, TiozinUnexpectedError
from tiozin.utils import helpers

from .plugin_scanner import PluginScanner

T = TypeVar("T", bound=PlugIn)


class PluginFactory(Resource):
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
        self._index: dict[str, type[PlugIn] | set[type[PlugIn]]] = {}
        self._plugins: set[type[PlugIn]] = set()
        self.logger = self.logger.hide_none().hide_fields("description")

    def setup(self) -> None:
        for plugins in PluginScanner(self.logger).scan().values():
            for plugin in plugins:
                self.register(plugin)

    def register(self, plugin: type[PlugIn]) -> None:
        """
        Register a new plugin from a given provider namespace (e.g. `tio_pandas`, `tio_spark`)
        """
        if not helpers.is_plugin(plugin):
            raise TypeError(f"{plugin} is not a Plugin.")

        if plugin in self._plugins:
            return

        metadata = plugin.__tiometa__
        self._index.setdefault(metadata.name, set()).add(plugin)
        self._index[metadata.uri] = plugin
        self._index[metadata.tio_path] = plugin
        self._index[metadata.python_path] = plugin
        self._plugins.add(plugin)

    def load_plugin(self, kind: str, plugin_kind: type[T] | None = None, **args) -> PlugIn | T:
        """
        Resolve and loads a plugin by kind.

        The kind parameter accepts multiple formats for flexibility: simple class names
        like "MyPlugin", provider-qualified names like "tio_pandas:MyPlugin", or full
        Python paths like "my.module.MyPlugin". Use provider-qualified or Python paths to
        disambiguate when multiple plugins share the same class name.

        Args:
            kind: The Plugin identifier.
            plugin_kind: Restricts search to Input, Output, Transform, Runner, or Registry.
            **args: Plugin arguments forwarded to the plugin constructor.

        Raises:
            PluginNotFoundError: If the plugin does not exist or does not match the requested role.
            AmbiguousPluginError: If multiple plugins match the kind without a unique identifier.

        Returns:
            A new instance of the resolved plugin.
        """
        candidates = helpers.as_list(self._index.get(kind))

        if not candidates:
            raise PluginNotFoundError(kind)

        if len(candidates) > 1:
            raise AmbiguousPluginError(kind, [p.__tiometa__.tio_path for p in candidates])

        plugin = candidates[0]
        plugin_name = plugin.__tiometa__.name

        if plugin_kind and not issubclass(plugin, plugin_kind):
            raise PluginNotFoundError(kind, detail=f"{plugin_name} is not a {plugin_kind}.")

        self.info(f"Loading {plugin_name} with args", **args)
        return plugin(**args)

    def load_job(self, kind: str, **args) -> Job:
        """
        Load and instantiate a Job plugin by kind.

        This method resolves the Job plugin associated with the given kind and
        returns a new Job instance using the provided arguments.
        """
        return self.load_plugin(kind, Job, **args)

    def load_manifest(self, manifest: Manifest | PlugIn) -> PlugIn:
        """
        Load and instantiate a job step from a manifest.

        This method resolves and instantiates the appropriate operator plugin
        (Input, Output, Transform, or Runner) based on the manifest type.
        If an operator instance is provided, it is returned unchanged.
        """
        if isinstance(manifest, PlugIn):
            return manifest

        args = manifest.model_dump()
        kind = args.pop("kind")

        match manifest:
            case RunnerManifest():
                return self.load_plugin(kind, Runner, **args)
            case InputManifest():
                return self.load_plugin(kind, Input, **args)
            case TransformManifest():
                return self.load_plugin(kind, Transform, **args)
            case OutputManifest():
                return self.load_plugin(kind, Output, **args)
            case _:
                raise TiozinUnexpectedError(f"Unsupported manifest: {type(manifest).__name__}")
