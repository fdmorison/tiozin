from tiozin import SettingRegistry, env
from tiozin.api import Loggable, Registry
from tiozin.compose.assembly.tiozin_registry import tiozin_registry


class Lifecycle(Loggable):
    """
    Manages application lifecycle for registries.

    Handles setup and shutdown of all registered components.
    """

    def __init__(self, settings_file: str = None) -> None:
        super().__init__()
        self.ready = False
        self.settings_file = settings_file
        self.registries: list[Registry] = []

    def setup(self) -> None:
        setting_registry: SettingRegistry = tiozin_registry.load(
            kind=env.TIO_SETTING_REGISTRY_KIND,
            location=self.settings_file or env.TIO_SETTING_REGISTRY_LOCATION,
            timeout=env.TIO_SETTING_REGISTRY_TIMEOUT,
            readonly=env.TIO_SETTING_REGISTRY_READONLY,
            cache=env.TIO_SETTING_REGISTRY_CACHE,
        )
        self._setup_registry(setting_registry)

        setting_registry = setting_registry.delegate()
        self._setup_registry(setting_registry)

        registries = setting_registry.get().registries

        self.setting_registry = setting_registry
        self.secret_registry = tiozin_registry.load_manifest(registries.secret)
        self.schema_registry = tiozin_registry.load_manifest(registries.schema)
        self.transaction_registry = tiozin_registry.load_manifest(registries.transaction)
        self.job_registry = tiozin_registry.load_manifest(registries.job)
        self.metric_registry = tiozin_registry.load_manifest(registries.metric)
        self.lineage_registry = tiozin_registry.load_manifest(registries.lineage)

        self.registries += [
            self.setting_registry,
            self.secret_registry,
            self.schema_registry,
            self.transaction_registry,
            self.job_registry,
            self.metric_registry,
            self.lineage_registry,
        ]

        for registry in self.registries:
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
        for registry in reversed(self.registries):
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
