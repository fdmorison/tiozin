import logging

from .registry import MetadataRegistry


class Lifecycle:
    """
    Manages application lifecycle for registries.

    Handles setup and shutdown of all registered components.
    """

    def __init__(self, *registries: MetadataRegistry):
        self.name = type(self).__name__
        self.logger = logging.getLogger(self.name)
        self.ready = False
        self.registries = tuple(registries)

    def setup(self) -> None:
        for registry in self.registries:
            try:
                self.logger.info(f"🟣 {registry} is starting.")
                registry.setup()
                registry.ready = True
                self.logger.info(f"🟢 {registry} is ready.")
            except Exception as e:
                self.logger.error(f"🚨 {registry} setup failed: {e}.")
                raise

        self.ready = True

    def shutdown(self) -> None:
        for registry in reversed(self.registries):
            try:
                if registry.ready:
                    registry.shutdown()
                    self.logger.info(f"🛑 {registry} shutdown is successful.")
                else:
                    self.logger.info(f"🛑 {registry} shutdown skipped (uninitialized).")
            except Exception:
                self.logger.exception(f"🚨 {registry} shutdown failed.")
            finally:
                registry.ready = False
