from __future__ import annotations

from dataclasses import dataclass

from tiozin.assembly.template_context_builder import TemplateContextBuilder

from .context import Context
from .job_context import JobContext


@dataclass
class StepContext(Context):
    """
    Runtime context representing the execution of a single step within a job.

    StepContext is created when an Input, Transform, or Output step starts running.
    It represents the execution environment of that step and provides access to
    both step-specific information and shared job-level context.

    Each StepContext is associated with a parent JobContext, from which it inherits
    template variables, shared session state, and the nominal time reference.

    In simple terms, StepContext answers:
    “Which step is running, as part of which job, and under which metadata?”

    StepContext provides:
    - A reference to the parent JobContext
    - Step identity and domain metadata (organization, domain, product, model, etc.)
    - Access to shared session state between job, runner, and steps
    - Runtime timestamps for logging, metrics, and observability
    - A step-level view of template variables derived from the job context

    StepContext does not manage execution flow or dependencies. It does not schedule
    steps or control their order. It simply represents the runtime context of a
    single step execution within a job.
    """

    job: JobContext

    def __post_init__(self) -> None:
        self.session = self.job.session

        if self.temp_workdir is None:
            self.temp_workdir = self.job.temp_workdir / self.name
            self.temp_workdir.mkdir(parents=True, exist_ok=True)

        self.template_vars = (
            TemplateContextBuilder()
            .with_defaults(self.job.template_vars)
            .with_variables(self.template_vars)
            .build()
        )

        super().__post_init__()
