import importlib
import inspect
import pkgutil
from importlib.metadata import EntryPoint, entry_points
from types import ModuleType

from tiozin import config
from tiozin.api import Loggable, Tiozin

from .. import reflection
from ..policies import FamilyNamePolicy


class TiozinScanner(Loggable):
    """
    Scans provider families to discover Tiozin plugins.

    The TiozinScanner is responsible only for discovery. It walks families packages declared via
    entry points lookinf for Tios or Tias and collects concrete Tiozin plugins.

    The scanner does not register, instantiate, validate, or resolve Tiozin plugins. It only returns
    discovered classes grouped by family name.
    """

    def _scan_families(self) -> list[tuple[EntryPoint, ModuleType]]:
        families: list[tuple[EntryPoint, ModuleType]] = []

        for entrypoint in entry_points(group=config.tiozin_family_group):
            # Family name must follow policy
            if not FamilyNamePolicy.eval(entrypoint).ok():
                continue

            # Family must load successfully
            try:
                family = entrypoint.load()
            except Exception as e:
                self.exception(f"💥 Family `{entrypoint.name}` failed to load: {e}")
                continue

            # Family must be a package
            if not reflection.is_package(family):
                self.warning(
                    f"🧓 Skipping family `{entrypoint.name}` because it is not a package: {family}"
                )
                continue

            self.info(f"🧓 Family `{entrypoint.name}` discovered")
            families.append((entrypoint, family))

        return families

    def _scan_tiozins(self, family: ModuleType) -> list[type[Tiozin]]:
        tiozins: set[type[Tiozin]] = set()

        for _, module_name, _ in pkgutil.walk_packages(
            family.__path__,
            family.__name__ + ".",
        ):
            try:
                module = importlib.import_module(module_name)
                for _, clazz in inspect.getmembers(module, inspect.isclass):
                    if clazz.__module__ == module_name and reflection.is_tiozin(clazz):
                        tiozins.add(clazz)
                        self.debug(f"🧝 Tiozin `{clazz.tiozin_name}` discovered")
            except ImportError as e:
                # Tiozin plugins may have optional or environment-specific dependencies.
                # Thus, ImportError is ignored by design during discovery.
                self.debug(
                    f"Skipping module `{module_name}` during plugin discovery "
                    f"because an optional dependency is missing: {e}"
                )

        return list(tiozins)

    def scan(self) -> dict[str, list[type[Tiozin]]]:
        """
        Discovers all Tiozin plugins grouped by Family name.

        Returns:
            Mapping of Family to list of Tiozins.
        """
        tiozins_per_family: dict[str, list[type[Tiozin]]] = {}

        for family, package in self._scan_families():
            tiozins_per_family[family.name] = self._scan_tiozins(package)

        return tiozins_per_family
