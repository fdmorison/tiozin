import importlib
import inspect
import pkgutil
from importlib.metadata import EntryPoint, entry_points
from types import ModuleType

from tiozin import config
from tiozin.api import Loggable, PlugIn
from tiozin.assembly.policies import ProviderNamePolicy
from tiozin.utils import reflection


class PluginScanner(Loggable):
    """
    Scans plugin provider packages to discover plugin classes.

    The PluginScanner is responsible only for *discovery*. It walks provider
    packages declared via entry points, loads their modules, and collects
    concrete plugin classes that match the expected plugin contract.

    The scanner does not register, instantiate, validate, or resolve plugins.
    It only returns discovered plugin classes grouped by provider name.
    """

    def _scan_providers(self) -> list[tuple[EntryPoint, ModuleType]]:
        providers: list[tuple[EntryPoint, ModuleType]] = []

        for tio in entry_points(group=config.plugin_provider_group):
            # Provider name must follow policy
            if not ProviderNamePolicy.eval(tio).ok():
                continue

            # Provider must load successfully
            try:
                package = tio.load()
            except Exception as e:
                self.exception(f"💥 Provider `{tio.name}` failed to load: {e}", exc_info=True)
                continue

            # Provider must be a package
            if not reflection.is_package(package):
                self.warning(
                    f"🧓 Skipping provider `{tio.name}` because it is not a package: {package}"
                )
                continue

            self.info(f"🧓 Provider `{tio.name}` discovered")
            providers.append((tio, package))

        return providers

    def _scan_plugins(self, tio_package: ModuleType) -> list[type[PlugIn]]:
        plugins: set[type[PlugIn]] = set()

        for _, module_name, _ in pkgutil.walk_packages(
            tio_package.__path__,
            tio_package.__name__ + ".",
        ):
            try:
                module = importlib.import_module(module_name)
                for _, clazz in inspect.getmembers(module, inspect.isclass):
                    if clazz.__module__ == module_name and reflection.is_plugin(clazz):
                        plugins.add(clazz)
            except ImportError:
                # Plugins may have optional or environment-specific dependencies.
                # Thus, ImportError is ignored by design during discovery.
                pass

        return list(plugins)

    def scan(self) -> dict[str, list[type[PlugIn]]]:
        """
        Discover all plugins grouped by provider name.

        Returns:
            Mapping of provider name -> list of plugin classes
        """
        plugins: dict[str, list[type[PlugIn]]] = {}

        for tio, tio_package in self._scan_providers():
            plugins[tio.name] = self._scan_plugins(tio_package)

        return plugins
