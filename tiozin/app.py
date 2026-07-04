import atexit
import signal

import wrapt

from . import logs
from .api import Context, Job, JobManifest
from .api.loggable import Loggable
from .api.metadata.bundle import Registries
from .container import AppContainer
from .exceptions import TiozinInputError
from .status import AppStatus
from .utils import as_flat_list
from .utils.decorators import ensure_setup

JobInput = str | JobManifest | Job


@ensure_setup
class TiozinApp(Loggable):
    """
    Main application entrypoint for Tiozin.

    Initializes the framework to run jobs. Handles registry setup, context initialization, and
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
        """
        Boots the framework: installs shutdown hooks and starts the registries.

        Idempotent — returns immediately if the application is already ready.
        """
        if self._status.is_ready():
            return

        self.info("Application is starting.")
        self._status = self._status.set_booting()

        # Install shutdown hooks
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
        """
        Shuts the framework down, tearing the registries down.

        Idempotent — returns immediately if the application is already shut down.
        """
        if self._status.is_shutdown():
            return
        self.info("Application is shutting down...")
        self._containers.teardown()
        self._status = self._status.set_shutdown()
        self.info("Application shutdown completed.")

    def resolve_manifest(self, job: str | JobManifest) -> JobManifest:
        """
        Resolves any job input into a `JobManifest`.

        A `JobManifest` is returned as is. A string is first parsed as YAML/JSON content, then
        falls back to a registry lookup by identifier. Raises `TiozinInputError` if it cannot be
        resolved.
        """
        if isinstance(job, JobManifest):
            return job

        manifest = JobManifest.try_from_yaml(job)
        manifest = manifest or self._containers.registries.job.get(job)

        TiozinInputError.raise_if(
            manifest is None,
            f"Invalid job: {job}.",
        )
        return manifest

    def validate(self, *jobs: str) -> None:
        """
        Validates one or more jobs without running them.

        Accepts YAML/JSON content strings or job identifier strings. Resolves each manifest
        without building or submitting the job. Raises `TiozinInputError` on the first invalid
        job; returns cleanly if all are valid.
        """
        for job in as_flat_list(*jobs):
            self.resolve_manifest(job)

    def run(self, *jobs: JobInput) -> list[object]:
        """
        Runs one or more jobs in sequence.

        Accepts one or more jobs as positional arguments, or a single list. Each item may be a
        `Job` instance, a `JobManifest`, a YAML/JSON string, or a job identifier string. Returns
        the list of job results, one per input.
        """
        results = []

        for job in as_flat_list(*jobs):
            if isinstance(job, (str, JobManifest)):
                manifest = self.resolve_manifest(job)
                job = Job.builder().from_manifest(manifest).build()

            TiozinInputError.raise_if(
                not isinstance(job, Job),
                f"Invalid job: {job}.",
            )

            with Context.for_job(job, registries=self._containers.registries):
                data = job.submit()
                results.append(data)

        return results


logs.setup()
