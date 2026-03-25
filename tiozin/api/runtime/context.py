from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar, Token
from dataclasses import dataclass, field, fields
from pathlib import Path
from types import MappingProxyType as FrozenMapping
from typing import TYPE_CHECKING, Any

from pendulum import DateTime

from tiozin.api.metadata.bundle import Registries
from tiozin.compose import TemplateDate, TemplateEnv, TemplateSecret
from tiozin.compose.templating.filters import JINJA
from tiozin.exceptions import TiozinInternalError
from tiozin.utils import create_local_temp_dir, generate_id, utcnow

if TYPE_CHECKING:
    from tiozin import EtlStep, Job, Runner, Tiozin


_current_context: ContextVar[Context | None] = ContextVar(
    "tiozin_current_context",
    default=None,
)


@dataclass(slots=True, kw_only=True)
class Context:
    """
    Represents the execution scope of a job or step.

    Context stores identity, domain, governance, runner, and runtime state
    for the current execution.

    It works as a standard Python context manager. When activated with
    `with context:`, it becomes the active execution scope and can be
    accessed anywhere in the call stack.

    Creating a context:

        context = Context.for_job(job)
        context = Context.for_step(step)
        child = context.for_child_step(step)

    Context activation (handled automatically by proxies):

        with context:
            ...

    Accessing the active context inside a plugin:

        ctx = self.context                     # raises if not active; recommended
        ctx = Context.current()                # raises if not active
        ctx = Context.current(required=False)  # returns None if not active
    """

    # ==================================================
    # Root reference (set by factory methods)
    # ==================================================
    job: Context = field(init=False, repr=False)

    # ==================================================
    # Identity
    # ==================================================
    name: str
    slug: str
    kind: str
    tiozin_role: str

    # ==================================================
    # Domain
    # ==================================================
    org: str
    region: str
    domain: str
    subdomain: str
    layer: str
    product: str
    model: str

    # ==================================================
    # Ownership
    # ==================================================
    maintainer: str | None = None
    cost_center: str | None = None
    owner: str | None = None
    labels: dict[str, str] = field(default_factory=dict)

    # ==================================================
    # Tiozin arguments
    # ==================================================
    options: dict[str, Any]

    # ==================================================
    # Runtime Identity
    # ==================================================
    run_id: str = field(init=False)
    run_attempt: int = field(default=1)
    nominal_time: DateTime = field(init=False)

    # ==================================================
    # Runtime Lifecycle
    # ==================================================
    runner: Runner = field(default=None, metadata={"template": False})
    setup_at: DateTime | None = field(default=None, metadata={"template": False})
    executed_at: DateTime | None = field(default=None, metadata={"template": False})
    teardown_at: DateTime | None = field(default=None, metadata={"template": False})
    finished_at: DateTime | None = field(default=None, metadata={"template": False})

    # ==================================================
    # Registries
    # ==================================================
    registries: Registries = field(
        default_factory=Registries, repr=False, metadata={"template": False}
    )

    # ==================================================
    # Infra
    # ==================================================
    temp_workdir: Path = field(init=False)

    shared: dict[str, Any] = field(
        repr=False,
        default_factory=dict,
        metadata={"template": False},
    )

    template_vars: Mapping[str, Any] = field(
        init=False,
        repr=False,
        default_factory=dict,
        metadata={"template": False},
    )

    _tokens: list[Token] = field(
        init=False,
        repr=False,
        default_factory=list,
        metadata={"template": False},
    )

    # ==================================================
    # Factories
    # ==================================================

    @classmethod
    def for_job(cls, job: Job, registries: Registries = None) -> Context:
        ctx = cls(
            # Identity — always from job
            name=job.name,
            slug=job.slug,
            kind=job.tiozin_name,
            tiozin_role=job.tiozin_role,
            # Domain — always from job
            org=job.org,
            region=job.region,
            domain=job.domain,
            subdomain=job.subdomain,
            layer=job.layer,
            product=job.product,
            model=job.model,
            # Ownership — always from job
            maintainer=job.maintainer,
            cost_center=job.cost_center,
            owner=job.owner,
            labels=job.labels,
            # Arguments — always from job
            options=job.options,
            # Runtime — injected externally (eg: from TiozinApp, tests, etc)
            registries=registries or Registries(),
        )
        ctx.job = ctx
        ctx.runner = job.runner
        ctx.run_id = generate_id(prefix="job")
        ctx.nominal_time = utcnow()
        ctx.temp_workdir = create_local_temp_dir(job.slug, ctx.run_id)
        ctx._build_template_vars()
        return ctx

    @classmethod
    def for_step(cls, step: EtlStep, registries: Registries = None) -> Context:
        parent = cls.current(required=False)

        if parent:
            if parent.belongs_to(step):
                return parent
            return parent.for_child_step(step)

        ctx = cls(
            # Identity — always from step
            name=step.name,
            slug=step.slug,
            kind=step.tiozin_name,
            tiozin_role=step.tiozin_role,
            # Domain — always from step
            org=step.org,
            region=step.region,
            domain=step.domain,
            subdomain=step.subdomain,
            layer=step.layer,
            product=step.product,
            model=step.model,
            # Ownership — not available at step level
            maintainer=None,
            cost_center=None,
            owner=None,
            labels={},
            # Arguments — always from step
            options=step.options,
            # Runtime — injected externally  (eg: tests, etc)
            registries=registries or Registries(),
        )
        ctx.job = None
        ctx.runner = None
        ctx.run_id = cls._generate_step_run_id(step.slug)
        ctx.nominal_time = utcnow()
        ctx.temp_workdir = create_local_temp_dir(step.slug, ctx.run_id)
        ctx._build_template_vars()
        return ctx

    def for_child_step(self, step: EtlStep) -> Context:
        ctx = Context(
            # Identity — always from step
            name=step.name,
            slug=step.slug,
            kind=step.tiozin_name,
            tiozin_role=step.tiozin_role,
            # Arguments — always from step
            options=step.options,
            # Domain — step value, fallback to parent
            org=step.org or self.org,
            region=step.region or self.region,
            domain=step.domain or self.domain,
            subdomain=step.subdomain or self.subdomain,
            layer=step.layer or self.layer,
            product=step.product or self.product,
            model=step.model or self.model,
            # Ownership — always inherited from parent
            maintainer=self.maintainer,
            cost_center=self.cost_center,
            owner=self.owner,
            labels=self.labels,
            # Runtime — always inherited from parent
            shared=self.shared,
            registries=self.registries,
        )
        ctx.job = self.job
        ctx.runner = self.job.runner
        ctx.run_id = self._generate_step_run_id(step.slug, self.job)
        ctx.nominal_time = self.job.nominal_time
        ctx.temp_workdir = create_local_temp_dir(self.job.temp_workdir, step.slug)
        ctx._build_template_vars(base=self.template_vars)
        return ctx

    # ==================================================
    # Context Management
    # ==================================================

    def __enter__(self) -> Context:
        """
        Activate this Context as the current execution scope.

        Context is reentrant and supports nested activation. Each
        __enter__ call pushes a new ContextVar token onto an internal
        stack, and __exit__ restores the previous scope accordingly.
        """
        token = _current_context.set(self)
        self._tokens.append(token)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """
        Deactivate the current execution scope and restore the previous one.

        Supports nested scopes by popping the most recent activation token.
        """
        if not self._tokens:
            return
        token = self._tokens.pop()
        _current_context.reset(token)

    # ==================================================
    # Utilities
    # ==================================================

    @staticmethod
    def current(required: bool = True) -> Context | None:
        ctx = _current_context.get()
        TiozinInternalError.raise_if(
            required and ctx is None,
            "Tiozin has no active execution context",
        )
        return ctx

    def belongs_to(self, plugin: Tiozin) -> bool:
        return self.slug == plugin.slug and self.kind == plugin.tiozin_name

    def render(self, value: str) -> str:
        return JINJA.from_string(value).render(self.template_vars)

    @property
    def is_root(self) -> bool:
        return self.job is self

    @property
    def namespace(self) -> str:
        return f"{self.org}.{self.region}.{self.domain}.{self.subdomain}"

    @property
    def dataset(self) -> str:
        return f"{self.layer}.{self.product}.{self.model}"

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

    # ==================================================
    # Private Utilities
    # ==================================================
    @staticmethod
    def _generate_step_run_id(slug: str, job: Context | None = None) -> str:
        if job:
            job_run_id = job.run_id.removeprefix("job_")
            return f"step_{job_run_id}"
        return generate_id(prefix="step")

    def _build_template_vars(self, base: Mapping[str, Any] | None = None) -> None:
        result = dict(self.template_vars)

        # defaults
        if base:
            result |= base

        # context fields
        context_data = {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.metadata.get("template", True)
        }
        result |= context_data

        # Template Acessors
        now = TemplateDate()
        result |= now.to_dict()
        result["DAY"] = now
        result["ENV"] = TemplateEnv()
        result["SECRET"] = TemplateSecret(self.registries.secret) if self.registries.secret else {}
        self.template_vars = FrozenMapping(result)
