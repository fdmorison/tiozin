import atexit
import signal
from threading import RLock

from tiozin import Job, Resource, logs
from tiozin.api.metadata.job_manifest import JobManifest
from tiozin.assembly.registry_factory import RegistryFactory
from tiozin.exceptions import TiozinError
from tiozin.lifecycle import Lifecycle
from tiozin.utils.app_status import AppStatus


class TiozinApp(Resource):
    """
    Main application entrypoint for Tiozin.

    Coordinates job execution and manages the application lifecycle,
    including registry initialization, context setup, and graceful
    startup and shutdown handling.

    Jobs are resolved from the job registry, built from manifests,
    and executed under a controlled runtime environment.
    """

    def __init__(self, registries: RegistryFactory = None) -> None:
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
                def on_signal(signum, _) -> None:
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

    def teardown(self) -> None:
        with self.lock:
            if self.status.is_app_finished():
                return

            self.info(f"{self.status.capitalize()} Application is shutting down...")

            if self.status.is_running():
                self.current_job.teardown()
                self.lifecycle.teardown()
                self.status = self.status.set_canceled()
            else:
                self.lifecycle.teardown()
                self.status = self.status.set_completed()

            self.info("Application shutdown completed.")

    def run(self, job: str | JobManifest | Job) -> Job:
        """
        Run a job.

        This method accepts multiple input representations and normalizes them
        into a `Job` instance before execution.

        Supported input forms:
        - `Job`: Executed directly.
        - `JobManifest`: Used to build the job.
        - `str` (YAML/JSON): Parsed and validated as a manifest.
        - `str` (identifier): Resolved from the current job registry.

        The resolved job is executed within the application lifecycle.

        Args:
            job: A Job instance, JobManifest, YAML/JSON manifest string, or a job identifier.

        Returns:
            The job execution result, if any.

        Raises:
            JobNotFoundError: If the job identifier cannot be resolved.
            ManifestError: If the manifest string is invalid.
        """
        self.setup()

        with self.lock:
            try:
                self.current_job = None
                self.status = self.status.set_running()

                if isinstance(job, (str, JobManifest)):
                    manifest = JobManifest.try_from_yaml_or_json(job)
                    if manifest is None:
                        manifest = self.job_registry.get(identifier=job)
                    job = Job.builder().from_manifest(manifest).build()

                self.current_job = job
                result = job.execute()
                self.status = self.status.set_success()
                return result
            except TiozinError as e:
                self.status = self.status.set_failure()
                self.error(e.message)
                raise SystemExit(1) from e
            except Exception:
                self.status = self.status.set_failure()
                identifier = self.current_job.name if self.current_job else str(job)
                self.exception(f"Unexpected error while executing job `{identifier}`.")
                raise
            finally:
                self.current_job = None
