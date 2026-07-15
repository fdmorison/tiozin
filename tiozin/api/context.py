from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar, Token
from pathlib import Path
from types import MappingProxyType as FrozenMapping
from typing import TYPE_CHECKING, Any, Self

from pendulum import DateTime
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SkipValidation,
    ValidationInfo,
    field_validator,
    model_validator,
)

from tiozin.compose import TemplateDate, TemplateEnv, TemplateSecret
from tiozin.compose.templating.filters import JINJA
from tiozin.exceptions import TiozinInternalError
from tiozin.utils import create_local_temp_dir, utcnow

from .enums import Cadence
from .metadata.bundle import Registries
from .metadata.schema.model import Schema
from .runtime.catalog import RunCatalog
from .types import Attributes, Counter, NominalTime, Slug, TechnicalTime, TimeOrderedId

if TYPE_CHECKING:
    from tiozin import EtlStep, Job, Runner, Tiozin

    from .metadata.batch.base import BatchRegistry
    from .metadata.job.base import JobRegistry
    from .metadata.lineage.base import LineageRegistry
    from .metadata.metric.base import MetricRegistry
    from .metadata.schema.base import SchemaRegistry
    from .metadata.secret.base import SecretRegistry
    from .metadata.setting.base import SettingRegistry

SKIP_TEMPLATE = {"skip_template": True}


_current_context: ContextVar[Context | None] = ContextVar(
    "tiozin_current_Context",
    default=None,
)


class Context(BaseModel):
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

    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    _tokens: list[Token] = PrivateAttr(default_factory=list)

    # ==================================================
    # Root reference (set by factory methods)
    # ==================================================
    job: Context | None = Field(None, repr=False, frozen=True)

    # ==================================================
    # Identity
    # ==================================================
    name: str = Field(frozen=True)
    slug: Slug = Field(frozen=True)
    kind: str = Field(frozen=True)
    tiozin_role: str = Field(frozen=True)
    namespace: str | None = Field(default=None, frozen=True)

    # ==================================================
    # Domain / Product
    # ==================================================
    org: str = Field(frozen=True)
    region: str = Field(frozen=True)
    domain: str = Field(frozen=True)
    subdomain: str = Field(frozen=True)
    layer: str = Field(frozen=True)
    product: str = Field(frozen=True)
    model: str = Field(frozen=True)

    # ==================================================
    # Ownership
    # ==================================================
    maintainer: str | None = Field(default=None, frozen=True)
    cost_center: str | None = Field(default=None, frozen=True)
    owner: str | None = Field(default=None, frozen=True)
    labels: dict[str, str] = Field(default_factory=dict, frozen=True)

    # ==================================================
    # Extra Tiozin arguments
    # ==================================================
    options: Attributes = Field(frozen=True)

    # ==================================================
    # Runtime Identity
    # ==================================================
    run_id: TimeOrderedId = Field(frozen=True)
    run_attempt: Counter = 1
    cadence: Cadence = Field(default_factory=Cadence.current, frozen=True)
    nominal_time: NominalTime = Field(default_factory=utcnow, frozen=True)

    # ==================================================
    # Runtime Lifecycle
    # ==================================================
    runner: Runner | None = Field(None, frozen=True, json_schema_extra=SKIP_TEMPLATE)
    setup_at: TechnicalTime | None = Field(None, json_schema_extra=SKIP_TEMPLATE)
    executed_at: TechnicalTime | None = Field(None, json_schema_extra=SKIP_TEMPLATE)
    teardown_at: TechnicalTime | None = Field(None, json_schema_extra=SKIP_TEMPLATE)
    finished_at: TechnicalTime | None = Field(None, json_schema_extra=SKIP_TEMPLATE)

    # ==================================================
    # Metadata
    # ==================================================
    registries: Registries = Field(
        default_factory=Registries,
        frozen=True,
        repr=False,
        json_schema_extra=SKIP_TEMPLATE,
    )

    output_schema: Schema | None = Field(
        default=None,
        repr=False,
        json_schema_extra=SKIP_TEMPLATE,
    )

    # ==================================================
    # Infra
    # ==================================================
    temp_workdir: Path | None = Field(default=None, frozen=True)

    shared: SkipValidation[dict[str, Any]] = Field(
        default_factory=dict,
        frozen=True,
        repr=False,
        json_schema_extra=SKIP_TEMPLATE,
    )

    catalog: RunCatalog = Field(
        default_factory=RunCatalog,
        frozen=True,
        repr=False,
        json_schema_extra=SKIP_TEMPLATE,
    )

    template_vars: SkipValidation[Mapping[str, Any]] = Field(
        default_factory=dict,
        repr=False,
        json_schema_extra=SKIP_TEMPLATE,
    )

    # ==================================================
    # Initializers
    # ==================================================
    @field_validator("nominal_time", mode="after")
    def _init_nominal_time(cls, value: DateTime, info: ValidationInfo) -> DateTime:
        cadence: Cadence = info.data.get("cadence")
        return cadence.truncate(value)

    @model_validator(mode="after")
    def _init_job(self) -> Self:
        if self.is_job:
            self.__dict__["job"] = self
        return self

    @model_validator(mode="after")
    def _init_temp_workdir(self) -> Self:
        if self.temp_workdir:
            return self

        self.__dict__["temp_workdir"] = (
            create_local_temp_dir(self.qualified_slug, self.run_id)
            if self.is_root
            else create_local_temp_dir(self.job.temp_workdir, self.slug)
        )

        return self

    @model_validator(mode="after")
    def _init_template_vars(self) -> Self:
        result = dict(self.template_vars)

        # context fields
        context_data = {
            name: getattr(self, name)
            for name, info in type(self).model_fields.items()
            if not (info.json_schema_extra or {}).get("skip_template", False)
        }
        result |= context_data

        # Template Acessors
        now = TemplateDate()
        result |= now.to_dict()
        result["DAY"] = now
        result["ENV"] = TemplateEnv()
        result["SECRET"] = TemplateSecret(self.registries.secret) if self.registries.secret else {}
        self.__dict__["template_vars"] = FrozenMapping(result)
        return self

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
            namespace=job.namespace,
            # Ownership — always from job
            maintainer=job.maintainer,
            cost_center=job.cost_center,
            owner=job.owner,
            labels=job.labels,
            # Arguments — always from job
            options=job.options,
            # Runtime — run_id and nominal_time resolved by the types
            runner=job.runner,
            cadence=job.cadence,
            registries=registries or Registries(),
        )
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
            # Arguments — always from step
            options=step.options,
            # Runtime — cadence, run_id, and nominal_time fall back to defaults
            registries=registries or Registries(),
        )
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
            # Namespace — always inherited from parent
            namespace=self.namespace,
            # Ownership — always inherited from parent
            maintainer=self.maintainer,
            cost_center=self.cost_center,
            owner=self.owner,
            labels=self.labels,
            # Runtime — always inherited from parent
            job=self.job,
            runner=self.job.runner,
            cadence=self.job.cadence,
            nominal_time=self.job.nominal_time,
            shared=self.shared,
            catalog=self.catalog,
            registries=self.registries,
            template_vars=self.template_vars,
        )
        return ctx

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
    def is_job(self) -> bool:
        return self.tiozin_role == "Job"

    @property
    def is_step(self) -> bool:
        return self.tiozin_role in ("Input", "Transform", "Output")

    @property
    def is_root(self) -> bool:
        return self.job is self or self.job is None

    @property
    def qualified_slug(self) -> str:
        if self.is_root:
            return self.slug
        return f"{self.job.slug}.{self.slug}"

    @property
    def setting_registry(self) -> SettingRegistry:
        return self.registries.setting

    @property
    def secret_registry(self) -> SecretRegistry:
        return self.registries.secret

    @property
    def schema_registry(self) -> SchemaRegistry:
        return self.registries.schema

    @property
    def batch_registry(self) -> BatchRegistry:
        return self.registries.batch

    @property
    def job_registry(self) -> JobRegistry:
        return self.registries.job

    @property
    def metric_registry(self) -> MetricRegistry:
        return self.registries.metric

    @property
    def lineage_registry(self) -> LineageRegistry:
        return self.registries.lineage

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


def _rebuild() -> None:
    from tiozin.api.runtime.runner.base import Runner

    Context.model_rebuild(_types_namespace={"Runner": Runner})


_rebuild()
