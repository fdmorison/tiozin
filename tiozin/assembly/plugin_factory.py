from typing import TypeVar

from tiozin.api import Input, Job, Output, Plugable, Processor, Resource, Runner, Transform
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    Manifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.api.plugable import PluginMetadata
from tiozin.exceptions import AmbiguousPluginError, PluginNotFoundError, TiozinUnexpectedError
from tiozin.utils import helpers

from .plugin_scanner import PluginScanner

T = TypeVar("T", bound=Plugable)


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
        self._index: dict[str, type[Plugable] | set[type[Plugable]]] = {}
        self._plugins: set[type[Plugable]] = set()

    def setup(self, **kwargs) -> None:
        scanner = PluginScanner(self.logger)
        for tio_name, plugins in scanner.scan().items():
            for plugin in plugins:
                self.register(tio_name, plugin)

    def teardown(self, **kwargs) -> None:
        return None

    def register(self, provider: str, plugin: type[Plugable]) -> None:
        """
        Register a new plugin from a given provider namespace (e.g. `tio_pandas`, `tio_spark`)
        """
        if not helpers.is_plugin(plugin):
            raise TypeError(f"{plugin!r} is not a Plugin.")

        if plugin in self._plugins:
            return

        metadata = PluginMetadata(
            kind=plugin.__name__,
            tio_kind=f"{provider}:{plugin.__name__}",
            python_kind=f"{plugin.__module__}.{plugin.__qualname__}",
            provider=provider,
        )
        plugin.__tiometa__ = metadata
        self._index.setdefault(metadata.kind, set()).add(plugin)
        self._index[metadata.tio_kind] = plugin
        self._index[metadata.python_kind] = plugin
        self._plugins.add(plugin)

    def load_plugin(self, kind: str, plugin_kind: type[T] | None = None, **args) -> Plugable | T:
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
        plugin_or_candidates = self._index.get(kind)

        if not plugin_or_candidates:
            raise PluginNotFoundError(kind)

        if helpers.is_plugin(plugin_or_candidates):
            plugin = plugin_or_candidates
        else:
            if len(plugin_or_candidates) > 1:
                candidates = [p.__tiometa__.tio_kind for p in plugin_or_candidates]
                raise AmbiguousPluginError(kind, candidates)
            plugin = next(iter(plugin_or_candidates))

        if plugin_kind and not issubclass(plugin, plugin_kind):
            raise PluginNotFoundError(kind)

        return plugin(**args)

    def load_job(self, kind: str, **args) -> Job:
        """
        Load and instantiate a Job plugin by kind.

        This method resolves the Job plugin associated with the given kind and
        returns a new Job instance using the provided arguments.
        """
        return self.load_plugin(kind, Job, **args)

    def load_manifest(self, manifest: Manifest | Processor) -> Processor:
        """
        Load and instantiate a job step from a manifest.

        This method resolves and instantiates the appropriate operator plugin
        (Input, Output, Transform, or Runner) based on the manifest type.
        If an operator instance is provided, it is returned unchanged.
        """
        if isinstance(manifest, (Processor, Runner)):
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
