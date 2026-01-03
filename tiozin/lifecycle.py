from tiozin.api import Registry, Resource


class Lifecycle(Resource):
    """
    Manages application lifecycle for registries.

    Handles setup and shutdown of all registered components.
    """

    def __init__(self, *registries: Registry) -> None:
        super().__init__()
        self.ready = False
        self.registries = tuple(registries)

    def setup(self) -> None:
        for registry in self.registries:
            try:
                registry.setup()
                registry.ready = True
                self.info(f"🟢 {registry} is ready.")
            except Exception as e:
                self.error(f"🚨 {registry} setup failed: {e}.")
                raise
        self.ready = True

    def teardown(self) -> None:
        for registry in reversed(self.registries):
            try:
                if registry.ready:
                    registry.teardown()
                    self.logger.info(f"🛑 {registry} shutdown is successful.")
                else:
                    self.info(f"🛑 {registry} shutdown skipped (uninitialized).")
            except Exception:
                self.exception(f"🚨 {registry} shutdown failed.")
            finally:
                registry.ready = False
