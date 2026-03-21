import atexit
import signal

import wrapt

from tiozin.api.loggable import Loggable

from . import logs
from .api import Context, Job, JobManifest
from .api.metadata.bundle import Registries
from .container import AppContainer
from .exceptions import TiozinInputError, TiozinInternalError, TiozinUsageError
from .status import AppStatus
from .utils import as_flat_list

JobInput = str | JobManifest | Job


class TiozinApp(Loggable):
    """
    Main application entrypoint for Tiozin.

    Initializes the framework to runs jobs. Handles registry setup, context initialization, and
    graceful shutdown.
    """

    def __init__(self, settings_path: str = None) -> None:
        super().__init__()
        self._status = AppStatus.CREATED
        self._containers = AppContainer(settings_path)

    @property
    def registries(self) -> Registries:
        return self._containers.registries

    @wrapt.synchronized
    def setup(self) -> None:
        if self._status.is_ready():
            return

        self.info("Application is starting.")
        self._status = self._status.set_booting()

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
        self._containers.setup()
        self._status = self._status.set_ready()
        self.info("Application startup completed, ready to run jobs.")

    @wrapt.synchronized
    def teardown(self) -> None:
        if self._status.is_shutdown():
            return
        self.info("Application is shutting down...")
        self._containers.teardown()
        self._status = self._status.set_shutdown()
        self.info("Application shutdown completed.")

    def validate(self, *jobs: str) -> None:
        """
        Validates one or more job raw string manifests without running them.

        Accepts YAML/JSON content strings or job identifier strings.
        Parses and validates each manifest without building or submitting the job.
        """
        for job in as_flat_list(*jobs):
            try:
                self.setup()
                manifest = JobManifest.try_from_yaml_or_json(job)
                manifest = manifest or self._containers.registries.job.get(job)

                TiozinInputError.raise_if(
                    manifest is None,
                    f"Invalid job: {job}.",
                )

                self.info(f"✓ Job `{job}` is valid")
            except TiozinUsageError as e:
                self.error(e.message)
                raise

    def run(self, *jobs: JobInput) -> list[object]:
        """
        Runs one or more jobs in sequence.

        Accepts one or more jobs as positional arguments, or a single list.
        Each item may be a `Job` instance, a `JobManifest`, a YAML/JSON string,
        or a job identifier string.

        Returns the job result for a single job, or a list of results otherwise.
        """
        results = []

        for job in as_flat_list(*jobs):
            try:
                self.setup()

                if isinstance(job, (str, JobManifest)):
                    # Attempt yaml string or JobManifest
                    manifest = JobManifest.try_from_yaml_or_json(job)
                    # Attempt identifier string
                    manifest = manifest or self._containers.registries.job.get(job)
                    # Manifest is parsed, now build the job
                    job = Job.builder().from_manifest(manifest).build()

                TiozinInputError.raise_if(
                    not isinstance(job, Job),
                    f"Invalid job: {job}.",
                )

                with Context.for_job(job, registries=self._containers.registries):
                    data = job.submit()
                    results.append(data)

            except TiozinUsageError as e:
                self.error(e.message)
                raise
            except TiozinInternalError as e:
                self.exception(e.message)
                raise
            except Exception as e:
                self.exception("Unexpected error while executing job.")
                raise TiozinInternalError() from e

        return results


logs.setup()
