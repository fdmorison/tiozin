import atexit
import signal
from threading import RLock
from typing import NoReturn

from tiozin import logs
from tiozin.assembly.builder import JobBuilder
from tiozin.assembly.registry_factory import RegistryFactory
from tiozin.exceptions import TiozinException
from tiozin.lifecycle import Lifecycle
from tiozin.model import Component, Context, Job
from tiozin.utils.app_status import AppStatus


class TiozinApp(Component):
    """
    Main application entrypoint for Tiozin.

    Coordinates job execution and manages the application lifecycle,
    including registry initialization, context setup, and graceful
    startup and shutdown handling.

    Jobs are resolved from the job registry, built from manifests,
    and executed under a controlled runtime environment.
    """

    def __init__(self, registries: RegistryFactory = None) -> NoReturn:
        super().__init__()
        # Simple attributes
        self.status = AppStatus.CREATED
        self.current_job = None
        self.lock = RLock()
        # Registry management
        self.registries = registries or RegistryFactory()
        self.job_registry = self.registries.job_registry
        self.lifecycle = Lifecycle(*self.registries.all_registries())
        logs.setup()

    def setup(self) -> None:
        with self.lock:
            if self.status.is_ready():
                return

            try:
                self.info("Application is starting.")
                self.status = self.status.set_booting()

                # Install Shutdown hooks
                def on_signal(signum, _) -> NoReturn:
                    sigcode = signal.Signals(signum).name
                    self.warning(f"🚨 Interrupted by {sigcode}")
                    raise SystemExit(1)

                signal.signal(signal.SIGTERM, on_signal)
                signal.signal(signal.SIGINT, on_signal)
                signal.signal(signal.SIGHUP, on_signal)
                atexit.register(self.teardown)

                # Start registries
                self.lifecycle.setup()
                self.status = self.status.set_waiting()
                self.info("Application startup completed.")
            except Exception:
                self.status = self.status.set_failure()
                raise

    def teardown(self) -> NoReturn:
        with self.lock:
            if self.status.is_app_finished():
                return

            self.info(f"{self.status.capitalize()} Application is shutting down...")

            if self.status.is_running():
                self.current_job.stop()
                self.lifecycle.teardown()
                self.status = self.status.set_canceled()
            else:
                self.lifecycle.teardown()
                self.status = self.status.set_completed()

            self.info("Application shutdown completed.")

    def run(self, name: str) -> Job:
        """
        Executes a job by name.

        Resolves the job manifest from the registry, builds the job,
        and runs it within the application lifecycle.

        Args:
            name: Name of the job to execute.

        Returns:
            The executed job instance.
        """
        self.setup()

        with self.lock:
            try:
                self.status = self.status.set_running()
                context = Context(
                    lineage_registry=self.registries.lineage_registry,
                    metric_registry=self.registries.metric_registry,
                    schema_registry=self.registries.schema_registry,
                    secret_registry=self.registries.secret_registry,
                    transaction_registry=self.registries.transaction_registry,
                )
                manifest = self.job_registry.get(name)
                self.current_job = JobBuilder().from_manifest(manifest).build()
                self.current_job.run(context)
                self.status = self.status.set_success()
                return self.current_job
            except TiozinException as e:
                self.status = self.status.set_failure()
                self.error(e.message)
                SystemExit(1)
            except Exception:
                self.status = self.status.set_failure()
                self.exception(f"Unexpected error while executing job `{name}`. ")
                raise
