import importlib
import inspect
import pkgutil
from importlib.metadata import entry_points
from types import ModuleType
from typing import TypeVar

from tiozin import config
from tiozin.assembly.policies import ProviderNamePolicy
from tiozin.exceptions import AmbiguousPluginError, PluginNotFoundError
from tiozin.model import Input, Output, Plugable, Registry, Resource, Runner, Transform
from tiozin.model.plugable import PluginMetadata

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
        self.registry: dict[str, type[Plugable] | set[type[Plugable]]] = {}
        self.distinct: dict[str, type[Plugable]] = {}

    def _discover_tio_providers(self) -> None:
        """Discover and load all plugin providers from entry points."""
        for entrypoint in entry_points(group=config.plugin_provider_group):
            if not ProviderNamePolicy.eval(entrypoint).ok():
                continue
            tio_provider = entrypoint.load()
            self._discover_tio_plugins(tio_provider)

    def _discover_tio_plugins(self, tio: ModuleType) -> None:
        """Scan a provider module and register all plugin classes found."""
        tio_name = tio.__name__.split(".")[-1]
        for _, module_name, _ in pkgutil.walk_packages(tio.__path__, tio.__name__ + "."):
            try:
                module = importlib.import_module(module_name)
                for _, plugin in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(plugin, Plugable)
                        and plugin is not Plugable
                        and Plugable not in plugin.__bases__
                        and Registry not in plugin.__bases__
                        and not inspect.isabstract(plugin)
                    ):
                        self.register(tio_name, plugin)
            except (ImportError, ModuleNotFoundError):
                # Dependencies of optional provider may not be installed (e.g. tiozin[spark]).
                # In this case, we silently skip the provider plugins.
                pass

    def register(self, provider: str, plugin: type[Plugable]) -> None:
        """
        Register a new plugin.

        Args:
            provider: Provider namespace (e.g. `tio_pandas`, `tio_spark`, `tio_aws`).
            plugin: Plugin class to register.
        """
        if not issubclass(plugin, Plugable):
            raise TypeError(f"Invalid plugin class '{plugin}'. Plugins must subclass Plugable.")

        if plugin.__tiometa__:
            return

        metadata = PluginMetadata(
            kind=plugin.__name__,
            tio_kind=f"{provider}:{plugin.__name__}",
            python_kind=f"{plugin.__module__}.{plugin.__qualname__}",
            provider=provider,
        )
        plugin.__tiometa__ = metadata
        self.registry.setdefault(metadata.kind, set()).add(plugin)
        self.registry[metadata.tio_kind] = plugin
        self.registry[metadata.python_kind] = plugin
        self.distinct[metadata.python_kind] = plugin

    def get(self, kind: str, plugin_kind: type[T] | None = None, **args) -> Plugable | T:
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
        plugin_or_candidates = self.registry.get(kind)

        if not plugin_or_candidates:
            raise PluginNotFoundError(kind)

        if isinstance(plugin_or_candidates, type):
            plugin = plugin_or_candidates
        else:
            if len(plugin_or_candidates) > 1:
                candidates = [p.__tiometa__.tio_kind for p in plugin_or_candidates]
                raise AmbiguousPluginError(kind, candidates)
            plugin = next(iter(plugin_or_candidates))

        if plugin_kind and not issubclass(plugin, plugin_kind):
            raise PluginNotFoundError(kind)

        return plugin(**args)

    def get_input(self, kind: str, **args) -> Input:
        return self.get(kind, Input, **args)

    def get_output(self, kind: str, **args) -> Output:
        return self.get(kind, Output, **args)

    def get_transform(self, kind: str, **args) -> Transform:
        return self.get(kind, Transform, **args)

    def get_runner(self, kind: str, **args) -> Runner:
        return self.get(kind, Runner, **args)

    def get_registry(self, kind: str, **args) -> Registry:
        return self.get(kind, Registry, **args)
