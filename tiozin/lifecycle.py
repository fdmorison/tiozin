from tiozin.api import Loggable, Registry
from tiozin.compose.assembly.tiozin_registry import tiozin_registry
from tiozin.family.tio_kernel import FileSettingRegistry


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
        settings_registry = FileSettingRegistry(self.settings_file)
        self._setup_registry(settings_registry)

        settings_registry = settings_registry.delegate()
        self._setup_registry(settings_registry)

        manifest = settings_registry.get().registries
        self.job_registry = tiozin_registry.load_manifest(manifest.job)
        self.metric_registry = tiozin_registry.load_manifest(manifest.metric)
        self.lineage_registry = tiozin_registry.load_manifest(manifest.lineage)
        self.schema_registry = tiozin_registry.load_manifest(manifest.schema)
        self.transaction_registry = tiozin_registry.load_manifest(manifest.transaction)

        self.registries += [
            settings_registry,
            self.job_registry,
            self.metric_registry,
            self.lineage_registry,
            self.schema_registry,
            self.transaction_registry,
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
