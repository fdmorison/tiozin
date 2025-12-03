from .registry import Registry


class Lifecycle(Registry):
    """
    Manages the application lifecycle, including setup and proper shutdown off all registries.
    """

    def __init__(self):
        super().__init__()
        self.registries: list[Registry] = [
            # empty
        ]

    def setup(self):
        for registry in self.registries:
            try:
                self.logger.info(f"🟣 {registry} is starting")
                registry.setup()
                registry.ready = True
                self.logger.info(f"🟢 {registry} is ready")
            except Exception as e:
                self.logger.exception(f"🚨 {registry} setup failed: {e}")
                raise

        self.ready = True
        self.logger.info("🟢 All registries are ready.")

    def shutdown(self):
        for registry in reversed(self.registries):
            try:
                registry.shutdown()
                self.logger.info(f"🛑 {registry} shutdown is successful.")
            except Exception as e:
                self.logger.exception(f"🚨 {registry} shutdown failed: {e}")
        self.logger.info("🛑 Application shutdown completed.")


# Singleton Service Instance
lifecycle = Lifecycle()
