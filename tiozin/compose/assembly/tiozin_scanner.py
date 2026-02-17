import importlib
import inspect
import pkgutil
from importlib.metadata import EntryPoint, entry_points
from types import ModuleType

from tiozin import config
from tiozin.api import Loggable, Tiozin

from .. import reflection
from ..policies import ProviderNamePolicy


class TiozinScanner(Loggable):
    """
    Scans Tio provider packages to discover Tiozin plugins.

    The TiozinScanner is responsible only for discovery. It walks Tio packages declared via entry
    points, loads their modules, and collects concrete Tiozin plugins that match the expected
    contract.

    The scanner does not register, instantiate, validate, or resolve Tiozin plugins.
    It only returns discovered classes grouped by Tio name.
    """

    def _scan_tios(self) -> list[tuple[EntryPoint, ModuleType]]:
        tios: list[tuple[EntryPoint, ModuleType]] = []

        for tio in entry_points(group=config.tiozin_family_group):
            # Tio name must follow policy
            if not ProviderNamePolicy.eval(tio).ok():
                continue

            # Tio must load successfully
            try:
                package = tio.load()
            except Exception as e:
                self.exception(f"💥 Tio `{tio.name}` failed to load: {e}", exc_info=True)
                continue

            # Tio must be a package
            if not reflection.is_package(package):
                self.warning(f"🧓 Skipping Tio `{tio.name}` because it is not a package: {package}")
                continue

            self.info(f"🧓 Tio `{tio.name}` discovered")
            tios.append((tio, package))

        return tios

    def _scan_tiozins(self, tio_package: ModuleType) -> list[type[Tiozin]]:
        tiozins: set[type[Tiozin]] = set()

        for _, module_name, _ in pkgutil.walk_packages(
            tio_package.__path__,
            tio_package.__name__ + ".",
        ):
            try:
                module = importlib.import_module(module_name)
                for _, clazz in inspect.getmembers(module, inspect.isclass):
                    if clazz.__module__ == module_name and reflection.is_tiozin(clazz):
                        tiozins.add(clazz)
            except ImportError:
                # Tiozin plugins may have optional or environment-specific dependencies.
                # Thus, ImportError is ignored by design during discovery.
                pass

        return list(tiozins)

    def scan(self) -> dict[str, list[type[Tiozin]]]:
        """
        Discovers all Tiozin plugins grouped by Tio name.

        Returns:
            Mapping of Tio name to list of Tiozins.
        """
        result: dict[str, list[type[Tiozin]]] = {}

        for tio, tio_package in self._scan_tios():
            result[tio.name] = self._scan_tiozins(tio_package)

        return result
