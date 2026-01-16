from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .context import Context

if TYPE_CHECKING:
    from .job_context import JobContext


@dataclass
class RunnerContext(Context):
    """
    Runtime context representing the execution of a Runner within a job.

    RunnerContext is created when a Runner starts executing a job. It represents
    the runtime environment of the Runner and provides access to shared job-level
    context required to perform the execution.

    Each RunnerContext is associated with a parent JobContext, from which it
    inherits template variables, shared session state, and the nominal time
    reference used during execution.

    In simple terms, RunnerContext answers:
    “Which runner is executing this job, and under which job context?”

    RunnerContext provides:
    - A reference to the parent JobContext
    - Access to shared session state between the job, runner, and steps
    - Runtime timestamps for logging, metrics, and observability
    - A runner-level view of template variables derived from the job context

    RunnerContext does not define job logic or data transformations. It does not
    orchestrate execution or manage steps. It only represents the execution
    context of a Runner during a single job run.
    """

    # ------------------
    # Parent Job
    # ------------------
    job: JobContext
