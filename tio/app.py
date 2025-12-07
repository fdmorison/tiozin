import atexit
import logging
import signal

from wrapt import synchronized

from tio import config, logs
from tio.assembly.job_builder import JobBuilder
from tio.assembly.registry_factory import RegistryFactory
from tio.model.context import Context
from tio.model.enums import Status
from tio.registries import Lifecycle


class TioApp:

    def __init__(self, registries: RegistryFactory = None) -> None:
        self.name = config.app_name
        self.status = Status.PENDING
        self.logger = logging.getLogger(self.name)
        self.registries = registries or RegistryFactory()
        self.job_registry = self.registries.job_registry
        self.lifecycle = Lifecycle(*self.registries.all_registries())
        atexit.register(self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    @synchronized
    def setup(self) -> None:
        if not self.status.is_pending():
            return
        self.lifecycle.setup()
        self.status = self.status.set_running()

    @synchronized
    def shutdown(self, signum: int = None, frame=None) -> None:
        if signum:
            sig = signal.Signals(signum).name
            self.logger.warning(f"🚨 {config.app_title} was interrupted by {sig}")
            exit(1)

        self.lifecycle.shutdown()
        self.status = self.status.set_finished(self)

    @synchronized
    def run(self, job_uri: str) -> None:
        try:
            self.setup()
            context = Context(
                lineage_registry=self.registries.lineage_registry,
                metric_registry=self.registries.metric_registry,
                schema_registry=self.registries.schema_registry,
                secret_registry=self.registries.secret_registry,
                transaction_registry=self.registries.transaction_registry,
            )
            manifest = self.job_registry.get(job_uri)
            job = JobBuilder().from_yaml(manifest).build()
            job.run(context)
        except Exception:
            self.logger.exception(
                f"An unexpected error occurred while executing '{job_uri}'. "
                "Halting execution to prevent further impact."
            )
            raise

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'"{self.name}"'


logs.setup()
