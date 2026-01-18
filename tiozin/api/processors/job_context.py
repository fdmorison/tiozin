from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pendulum import DateTime

from tiozin.assembly.template_context_builder import TemplateContextBuilder
from tiozin.utils.helpers import utcnow

from .context import Context

if TYPE_CHECKING:
    from tiozin import Runner


@dataclass
class JobContext(Context):
    """
    Runtime context representing a single execution of a Job in Tiozin.

    JobContext is created when a job starts and carries all job-level information
    needed during execution. It includes metadata, runtime references, shared
    state, and the logical time used as a reference for data processing.

    This context is passed to the job and propagated to the runner and all steps,
    serving as the main source of job-level information during the run.

    In simple terms, JobContext answers:
    “Which job is running, with which metadata, and for which point in time?”

    JobContext provides:
    - Job identity, ownership, and organizational metadata
    - A reference to the Runner executing the job
    - A shared session for exchanging state between job, runner, and steps
    - Runtime timestamps for logging, metrics, and observability
    - A root scope of template variables used by all steps

    Nominal time:

    The `nominal_time` defines the logical time reference of the job. It represents
    the time slice of the data being processed, not necessarily the wall-clock
    execution time.

    Tiozin does not define schedules or execution frequency. When no external
    scheduler is used, `nominal_time` defaults to the wall-clock time at job start.
    Its meaning (daily, hourly, etc.) is defined by the job logic or an external
    orchestrator.

    All built-in date and time template variables are derived from `nominal_time`,
    ensuring deterministic behavior across retries, backfills, and replays.

    JobContext does not orchestrate execution. It only represents the execution
    environment of a single job run.
    """

    # ------------------
    # Fundamentals
    # -------------------
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str

    maintainer: str
    cost_center: str
    owner: str
    labels: dict[str, str]

    # ------------------
    # Runtime
    # ------------------
    runner: Runner = field(metadata={"template": False})
    nominal_time: DateTime = field(default_factory=utcnow)

    def __post_init__(self):
        super().__post_init__()
        self.template_vars = (
            TemplateContextBuilder()
            .with_context(self)
            .with_defaults(self.template_vars)
            .wiht_datetime(self.nominal_time)
            .build()
        )
