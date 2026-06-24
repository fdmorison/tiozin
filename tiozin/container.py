from tiozin.api import Registry, SettingRegistry
from tiozin.api.loggable import Loggable
from tiozin.api.metadata.bundle import Registries
from tiozin.api.metadata.setting.model import SettingRegistryManifest
from tiozin.compose.assembly.tiozin_registry import tiozin_registry


class AppContainer(Loggable):
    """
    Manages application lifecycle for registries.

    Handles setup and shutdown of all registered components.

    Attributes:
        ready: Whether the lifecycle has been fully set up.
        settings_path: Path to the settings file passed at construction time.
        registries: The registry bundle populated after `setup()`.
    """

    def __init__(self, settings_path: str = None) -> None:
        super().__init__()
        self.ready = False
        self.settings_path = settings_path
        self.registries: Registries = Registries()
        self._setup_order: list[Registry] = []

    def setup(self) -> None:
        defaults = SettingRegistryManifest()
        defaults.location = defaults.location or self.settings_path

        setting_registry = tiozin_registry.load(
            tiozin_role=SettingRegistry,
            **defaults.model_dump(),
        )
        setting_registry.setup()

        manifest = setting_registry.get()

        tiozin_registry.with_defaults(
            [e.model_dump() for e in manifest.runtime_defaults],
        )

        self.registries = Registries(
            setting=setting_registry,
            secret=tiozin_registry.load_manifest(manifest.registries.secret),
            schema=tiozin_registry.load_manifest(manifest.registries.schema),
            state=tiozin_registry.load_manifest(manifest.registries.state),
            job=tiozin_registry.load_manifest(manifest.registries.job),
            metric=tiozin_registry.load_manifest(manifest.registries.metric),
            lineage=tiozin_registry.load_manifest(manifest.registries.lineage),
        )

        self._setup_order = [
            self.registries.setting,
            self.registries.secret,
            self.registries.schema,
            self.registries.metric,
            self.registries.lineage,
            self.registries.state,
            self.registries.job,
        ]

        for registry in self._setup_order:
            registry.setup()
            if registry.ready:
                self.info(f"🟢 {registry} is ready.")

        self.ready = True

    def teardown(self) -> None:
        for registry in reversed(self._setup_order):
            registry.teardown()
            self.info(f"🛑 {registry} shutdown completed.")
        self.ready = False
