import atexit
import signal
from typing import NoReturn

from wrapt import synchronized

from tio import logs
from tio.assembly.job_builder import JobBuilder
from tio.assembly.registry_factory import RegistryFactory
from tio.model import Context, Job, Resource
from tio.registries import Lifecycle
from tio.status import AppStatus


class TioApp(Resource):
    """
    As the central hub of Tio's execution, TioApp assembles and runs one or more
    jobs, managing the ETL lifecycle in a graceful, predictable, and observable way.

    Once created, it acts as the application's coordination point for job
    resolution, context setup, lifecycle handling, and metadata registries.

    Custom registries may be injected through a RegistryFactory, allowing the
    application to be tested or initialized with custom components when needed.

    Typically, you create a TioApp instance in your entrypoint module like this:

        from tio.app import TioApp
        app = TioApp()

    Usage follows Tio's philosophy of simplicity: plug in the registries, call
    run(), and Tio handles the rest.
    """

    def __init__(self, registries: RegistryFactory = None) -> NoReturn:
        super().__init__()
        # Simple attributes
        self.status = AppStatus.CREATED
        self.current_job = None
        # Registry management
        self.registries = registries or RegistryFactory()
        self.job_registry = self.registries.job_registry
        self.lifecycle = Lifecycle(*self.registries.all_registries())

    @synchronized
    def setup(self) -> None:
        if self.status.is_ready():
            return

        try:
            self.logger.info("Application is starting.")
            self.status = self.status.set_booting()

            # Install Shutdown hooks
            def on_signal(signum, _) -> NoReturn:
                sigcode = signal.Signals(signum).name
                self.logger.warning(f"🚨 Interrupted by {sigcode}")
                raise SystemExit(1)

            signal.signal(signal.SIGTERM, on_signal)
            signal.signal(signal.SIGINT, on_signal)
            signal.signal(signal.SIGHUP, on_signal)
            atexit.register(self.shutdown)

            # Start registries
            self.lifecycle.setup()
            self.status = self.status.set_waiting()
            self.logger.info("Application startup completed.")
        except Exception:
            self.status = self.status.set_failure()
            raise

    @synchronized
    def shutdown(self) -> NoReturn:
        if self.status.is_app_finished():
            return

        self.logger.info(f"{self.status.capitalize()} Application is shutting down...")

        if self.status.is_running():
            self.current_job.stop()
            self.lifecycle.shutdown()
            self.status = self.status.set_canceled()
        else:
            self.lifecycle.shutdown()
            self.status = self.status.set_completed()

        self.logger.info("Application shutdown completed.")

    @synchronized
    def run(self, job_uri: str) -> Job:
        """
        Runs the job identified by the given URI.

        Resolves the job manifest from the job registry, builds the job, and
        executes it. Errors are logged and re-raised to avoid silent failures.

        Args:
            job_uri: The URI or identifier of the job to execute.

        Returns:
            The job instance that was executed.
        """
        self.setup()
        try:
            self.status = self.status.set_running()
            context = Context(
                lineage_registry=self.registries.lineage_registry,
                metric_registry=self.registries.metric_registry,
                schema_registry=self.registries.schema_registry,
                secret_registry=self.registries.secret_registry,
                transaction_registry=self.registries.transaction_registry,
            )
            manifest = self.job_registry.get(job_uri)
            self.current_job = JobBuilder().from_manifest(manifest).build()
            self.current_job.run(context)
            self.status = self.status.set_success()
            return self.current_job
        except Exception:
            self.status = self.status.set_failure()
            self.logger.exception(f"Unexpected error while executing job `{job_uri}`. ")
            raise


logs.setup()
