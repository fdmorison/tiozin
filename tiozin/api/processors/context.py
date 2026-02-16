from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pendulum import DateTime

from tiozin.compose.templating.context_builder import TemplateContextBuilder
from tiozin.utils import create_local_temp_dir, generate_id, utcnow

if TYPE_CHECKING:
    from tiozin import EtlStep, Job, Runner


@dataclass(kw_only=True)
class Context:
    """
    Runtime execution context used by all execution scopes in Tiozin.

    Context represents the execution environment for both jobs and steps.
    It provides identity, domain metadata, ownership, runtime state, and
    timing information required during execution.

    A Context can be either a root context (job-level) or a child context
    (step-level) linked to a parent. Child contexts inherit runtime attributes
    from their parent, including runner, session, ownership fields, and
    nominal time. This allows steps to access job-level information without
    duplication.

    In simple terms, Context answers:
    "What is executing, under which identity, and with which runtime state?"

    Context provides:
    - Execution identity (id, name, kind, plugin kind)
    - Domain metadata (org, region, domain, layer, product, model)
    - Ownership information (maintainer, cost_center, owner, labels)
    - Plugin options passed to the executing component
    - A shared template variable scope used during execution
    - A shared session dictionary for exchanging state across execution layers
    - A reference to the Runner executing the job
    - The nominal time reference for date-based template variables
    - Runtime timestamps for lifecycle tracking and observability
    - Helper properties for computing execution durations
    - A temporary directory path (temp_workdir) for intermediate files

    Hierarchy:
    - Root context (parent=None): Acts as job context, self.job points to self
    - Child context (parent=Context): Inherits from parent, self.job points to root

    Context is created and managed by Tiozin's runtime layer. User code should
    treat it as a read-only view of the execution environment, except for
    explicitly shared session state.
    """

    job: Context = None
    parent: Context = None

    # ------------------
    # Identity & Fundamentals
    # ------------------
    id: str = field(default_factory=generate_id)
    name: str
    kind: str
    plugin_kind: str
    options: Mapping[str, Any]

    maintainer: str = None
    cost_center: str = None
    owner: str = None
    labels: dict[str, str] = field(default_factory=dict)

    # ------------------
    # Domain Metadata
    # ------------------
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str

    # ------------------
    # Templating
    # ------------------
    template_vars: Mapping[str, Any] = field(default_factory=dict, metadata={"template": False})

    # ------------------
    # Shared state
    # ------------------
    session: Mapping[str, Any] = field(default_factory=dict, metadata={"template": False})

    # ------------------
    # Runtime
    # ------------------
    runner: Runner = field(default=None, metadata={"template": False})

    run_id: str = field(default_factory=generate_id)
    nominal_time: DateTime = field(default_factory=utcnow)
    setup_at: DateTime = None
    executed_at: DateTime = None
    teardown_at: DateTime = None
    finished_at: DateTime = None

    # ------------------
    # Temporary storage
    # ------------------
    temp_workdir: Path = field(default=None, metadata={"template": True})

    # ------------------
    # Initialize from parent
    # ------------------
    def __post_init__(self) -> None:
        parent = self.parent
        template_vars = TemplateContextBuilder()

        if not parent:
            self.job = self.job or self
            self.temp_workdir = create_local_temp_dir(self.name, self.run_id)
        else:
            self.job = parent.job
            self.temp_workdir = create_local_temp_dir(parent.temp_workdir, self.name)
            self.runner = parent.runner
            self.session = parent.session
            self.maintainer = parent.maintainer
            self.cost_center = parent.cost_center
            self.owner = parent.owner
            self.labels = parent.labels
            self.nominal_time = parent.nominal_time
            template_vars.with_defaults(parent.template_vars)

        self.template_vars = (
            template_vars.with_defaults(self.template_vars)
            .with_relative_date(self.nominal_time)
            .with_envvars()
            .with_context(self)
            .build()
        )

    @classmethod
    def from_step(cls, step: EtlStep, parent: Context = None) -> Context:
        return cls(
            # Parent
            parent=parent,
            # Identity
            name=step.name,
            kind=step.plugin_name,
            plugin_kind=step.plugin_kind,
            # Domain Metadata
            org=step.org,
            region=step.region,
            domain=step.domain,
            layer=step.layer,
            product=step.product,
            model=step.model,
            # Extra provider/plugin parameters
            options=step.options,
        )

    @classmethod
    def from_job(cls, job: Job) -> Context:
        return cls(
            # Parent
            parent=None,
            # Identity
            name=job.name,
            kind=job.plugin_name,
            plugin_kind=job.plugin_kind,
            # Domain Metadata
            org=job.org,
            region=job.region,
            domain=job.domain,
            layer=job.layer,
            product=job.product,
            model=job.model,
            # Ownership
            maintainer=job.maintainer,
            cost_center=job.cost_center,
            owner=job.owner,
            labels=job.labels,
            # Runtime
            runner=job.runner,
            # Extra provider/plugin parameters
            options=job.options,
        )

    # ------------------
    # Abstracts
    # ------------------
    def as_step_context(self, step: EtlStep) -> Context:
        return Context.from_step(step, parent=self.job)

    # ------------------
    # Timing helpers
    # ------------------
    @property
    def delay(self) -> float:
        now = utcnow()
        begin = self.setup_at or now
        end = self.finished_at or now
        return (end - begin).total_seconds()

    @property
    def setup_delay(self) -> float:
        now = utcnow()
        begin = self.setup_at or now
        end = self.executed_at or now
        return (end - begin).total_seconds()

    @property
    def execution_delay(self) -> float:
        now = utcnow()
        begin = self.executed_at or now
        end = self.teardown_at or now
        return (end - begin).total_seconds()

    @property
    def teardown_delay(self) -> float:
        now = utcnow()
        begin = self.teardown_at or now
        end = self.finished_at or now
        return (end - begin).total_seconds()
