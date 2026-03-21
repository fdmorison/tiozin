from tiozin import env
from tiozin.api import Registry, SettingRegistry
from tiozin.api.loggable import Loggable
from tiozin.api.metadata.bundle import Registries
from tiozin.compose.assembly.tiozin_factory import tiozin_factory


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
        self._boot_order: list[Registry] = []

    def setup(self) -> None:
        setting_registry = tiozin_factory.safe_load(
            tiozin_role=SettingRegistry,
            kind=env.TIO_SETTING_REGISTRY_KIND,
            location=self.settings_path or env.TIO_SETTING_REGISTRY_LOCATION,
            timeout=env.TIO_SETTING_REGISTRY_TIMEOUT,
            readonly=env.TIO_SETTING_REGISTRY_READONLY,
            cache=env.TIO_SETTING_REGISTRY_CACHE,
        )
        self._setup_registry(setting_registry)

        manifest = setting_registry.get()
        self.registries = Registries(
            setting=setting_registry,
            secret=tiozin_factory.load_manifest(manifest.registries.secret),
            schema=tiozin_factory.load_manifest(manifest.registries.schema),
            transaction=tiozin_factory.load_manifest(manifest.registries.transaction),
            job=tiozin_factory.load_manifest(manifest.registries.job),
            metric=tiozin_factory.load_manifest(manifest.registries.metric),
            lineage=tiozin_factory.load_manifest(manifest.registries.lineage),
        )

        self._boot_order = [
            self.registries.setting,
            self.registries.secret,
            self.registries.schema,
            self.registries.metric,
            self.registries.lineage,
            self.registries.transaction,
            self.registries.job,
        ]

        for registry in self._boot_order:
            self._setup_registry(registry)

        self.ready = True

    def _setup_registry(self, registry: Registry) -> None:
        try:
            if not registry.ready:
                registry.setup()
                registry.ready = True
                self.info(f"🟢 {registry.uri} is ready.")
        except Exception as e:
            self.error(f"🚨 {registry.uri} setup failed: {e}.")
            raise

    def teardown(self) -> None:
        for registry in reversed(self._boot_order):
            try:
                if registry.ready:
                    registry.teardown()
                    self.info(f"🛑 {registry.uri} shutdown is successful.")
                else:
                    self.info(f"🛑 {registry.uri} shutdown skipped (uninitialized).")
            except Exception:
                self.exception(f"🚨 {registry.uri} shutdown failed.")
            finally:
                registry.ready = False
