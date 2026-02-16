from unittest.mock import MagicMock

import pendulum
import pytest

from tiozin.api.processors.context import Context


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def job_context() -> Context:
    """Creates a root context (job-level) with all fields populated."""
    return Context(
        name="daily_orders",
        kind="LinearJob",
        plugin_kind="job",
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="daily",
        options={"retry": 3},
        maintainer="team-data",
        cost_center="cc-123",
        owner="alice@acme.com",
        labels={"env": "prod"},
        runner=MagicMock(),
        nominal_time=pendulum.parse("2026-01-15T00:00:00+00:00"),
        session={"shared": "data"},
    )


@pytest.fixture
def step_context(job_context: Context) -> Context:
    """Creates a child context (step-level) with a parent."""
    return Context(
        parent=job_context,
        name="read_orders",
        kind="NoOpInput",
        plugin_kind="read",
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="daily",
        options={"path": "/data/orders"},
    )


# =============================================================================
# Testing Context - Identity Fields
# =============================================================================
def test_context_should_have_identity_fields(job_context: Context):
    # Assert
    actual = (
        job_context.name,
        job_context.kind,
        job_context.plugin_kind,
        job_context.options,
    )
    expected = ("daily_orders", "LinearJob", "job", {"retry": 3})
    assert actual == expected


def test_context_should_generate_id_automatically():
    # Act
    context = Context(
        name="test",
        kind="test",
        plugin_kind="test",
        org="test",
        region="test",
        domain="test",
        layer="test",
        product="test",
        model="test",
        options={},
    )

    # Assert
    actual = (context.id is not None, len(context.id) > 0)
    expected = (True, True)
    assert actual == expected


def test_context_should_generate_run_id_automatically(job_context: Context):
    # Assert
    actual = (job_context.run_id is not None, len(job_context.run_id) > 0)
    expected = (True, True)
    assert actual == expected


# =============================================================================
# Testing Context - Domain Metadata
# =============================================================================
def test_context_should_have_domain_metadata(job_context: Context):
    # Assert
    actual = (
        job_context.org,
        job_context.region,
        job_context.domain,
        job_context.layer,
        job_context.product,
        job_context.model,
    )
    expected = ("acme", "latam", "sales", "raw", "orders", "daily")
    assert actual == expected


# =============================================================================
# Testing Context - Ownership
# =============================================================================
def test_context_should_have_ownership_fields(job_context: Context):
    # Assert
    actual = (
        job_context.maintainer,
        job_context.cost_center,
        job_context.owner,
        job_context.labels,
    )
    expected = ("team-data", "cc-123", "alice@acme.com", {"env": "prod"})
    assert actual == expected


# =============================================================================
# Testing Context - Nominal Time
# =============================================================================
def test_context_should_default_nominal_time_to_now():
    # Arrange
    before = pendulum.now("UTC")

    # Act
    context = Context(
        name="test",
        kind="test",
        plugin_kind="test",
        org="test",
        region="test",
        domain="test",
        layer="test",
        product="test",
        model="test",
        options={},
    )

    # Assert
    after = pendulum.now("UTC")
    assert before <= context.nominal_time <= after


def test_context_should_accept_custom_nominal_time():
    # Arrange
    custom_time = pendulum.parse("2026-06-15T12:00:00+00:00")

    # Act
    context = Context(
        name="test",
        kind="test",
        plugin_kind="test",
        org="test",
        region="test",
        domain="test",
        layer="test",
        product="test",
        model="test",
        options={},
        nominal_time=custom_time,
    )

    # Assert
    actual = context.nominal_time
    expected = custom_time
    assert actual == expected


# =============================================================================
# Testing Context - Runtime Timestamps
# =============================================================================
def test_context_should_have_null_timestamps_by_default(job_context: Context):
    # Assert
    actual = (
        job_context.setup_at,
        job_context.executed_at,
        job_context.teardown_at,
        job_context.finished_at,
    )
    expected = (None, None, None, None)
    assert actual == expected


# =============================================================================
# Testing Context - Timing Helpers
# =============================================================================
def test_context_delay_should_calculate_total_duration(job_context: Context):
    # Arrange
    job_context.setup_at = pendulum.parse("2026-01-15T10:00:00+00:00")
    job_context.finished_at = pendulum.parse("2026-01-15T10:00:05+00:00")

    # Act
    actual = job_context.delay

    # Assert
    expected = 5.0
    assert actual == expected


def test_context_setup_delay_should_calculate_setup_duration(job_context: Context):
    # Arrange
    job_context.setup_at = pendulum.parse("2026-01-15T10:00:00+00:00")
    job_context.executed_at = pendulum.parse("2026-01-15T10:00:02+00:00")

    # Act
    actual = job_context.setup_delay

    # Assert
    expected = 2.0
    assert actual == expected


def test_context_execution_delay_should_calculate_execution_duration(job_context: Context):
    # Arrange
    job_context.executed_at = pendulum.parse("2026-01-15T10:00:02+00:00")
    job_context.teardown_at = pendulum.parse("2026-01-15T10:00:10+00:00")

    # Act
    actual = job_context.execution_delay

    # Assert
    expected = 8.0
    assert actual == expected


def test_context_teardown_delay_should_calculate_teardown_duration(job_context: Context):
    # Arrange
    job_context.teardown_at = pendulum.parse("2026-01-15T10:00:10+00:00")
    job_context.finished_at = pendulum.parse("2026-01-15T10:00:11+00:00")

    # Act
    actual = job_context.teardown_delay

    # Assert
    expected = 1.0
    assert actual == expected


# =============================================================================
# Testing Context - Temporary Storage
# =============================================================================
def test_context_should_create_temp_workdir_automatically(job_context: Context):
    # Assert
    actual = (
        job_context.temp_workdir is not None,
        job_context.temp_workdir.exists(),
        job_context.temp_workdir.is_dir(),
    )
    expected = (True, True, True)
    assert actual == expected


def test_context_temp_workdir_should_be_organized_by_name_and_run_id(job_context: Context):
    # Assert
    path = str(job_context.temp_workdir)
    actual = (
        "/tiozin/" in path,
        f"/{job_context.name}/" in path,
        f"/{job_context.run_id}" in path,
    )
    expected = (True, True, True)
    assert actual == expected


def test_context_temp_workdir_should_be_in_template_vars(job_context: Context):
    # Assert
    actual = job_context.template_vars["temp_workdir"]
    expected = job_context.temp_workdir
    assert actual == expected


# =============================================================================
# Testing Context - Template Variables
# =============================================================================
def test_context_should_include_identity_fields_in_template_vars(job_context: Context):
    # Assert
    actual = (
        job_context.template_vars["id"],
        job_context.template_vars["name"],
        job_context.template_vars["kind"],
        job_context.template_vars["plugin_kind"],
    )
    expected = (job_context.id, "daily_orders", "LinearJob", "job")
    assert actual == expected


def test_context_should_include_domain_metadata_in_template_vars(job_context: Context):
    # Assert
    actual = (
        job_context.template_vars["org"],
        job_context.template_vars["region"],
        job_context.template_vars["domain"],
        job_context.template_vars["layer"],
        job_context.template_vars["product"],
        job_context.template_vars["model"],
    )
    expected = ("acme", "latam", "sales", "raw", "orders", "daily")
    assert actual == expected


def test_context_should_include_relative_date_vars_in_template_vars():
    # Arrange
    nominal_time = pendulum.parse("2026-06-15T12:00:00+00:00")

    # Act
    context = Context(
        name="test",
        kind="test",
        plugin_kind="test",
        org="test",
        region="test",
        domain="test",
        layer="test",
        product="test",
        model="test",
        options={},
        nominal_time=nominal_time,
    )

    # Assert
    actual = (
        str(context.template_vars["today"]),
        context.template_vars["YYYY"],
        context.template_vars["MM"],
        context.template_vars["DD"],
        context.template_vars["ds"],
    )
    expected = ("2026-06-15", "2026", "06", "15", "2026-06-15")
    assert actual == expected


def test_context_template_vars_should_include_fields_without_template_false(job_context: Context):
    # Assert
    expected = {
        "id",
        "name",
        "kind",
        "plugin_kind",
        "options",
        "run_id",
        "setup_at",
        "executed_at",
        "teardown_at",
        "finished_at",
        "temp_workdir",
        "org",
        "region",
        "domain",
        "layer",
        "product",
        "model",
        "maintainer",
        "cost_center",
        "owner",
        "labels",
        "nominal_time",
    }
    actual = {k for k in expected if k in job_context.template_vars}
    assert actual == expected


def test_context_template_vars_should_exclude_fields_with_template_false(job_context: Context):
    # Assert
    excluded = {"runner", "template_vars", "session"}
    actual = {k for k in excluded if k in job_context.template_vars}
    expected = set()
    assert actual == expected


def test_context_template_vars_should_be_immutable(job_context: Context):
    # Assert
    with pytest.raises(TypeError):
        job_context.template_vars["new_key"] = "value"


# =============================================================================
# Testing Context - Parent/Child Hierarchy
# =============================================================================
def test_context_should_reference_itself_as_job_when_root(job_context: Context):
    # Assert
    actual = job_context.job
    expected = job_context
    assert actual is expected


def test_context_should_reference_parent_job_when_child(
    step_context: Context, job_context: Context
):
    # Assert
    actual = step_context.job
    expected = job_context
    assert actual is expected


def test_context_should_inherit_session_from_parent(step_context: Context, job_context: Context):
    # Assert
    actual = step_context.session
    expected = job_context.session
    assert actual is expected


def test_context_should_inherit_runner_from_parent(step_context: Context, job_context: Context):
    # Assert
    actual = step_context.runner
    expected = job_context.runner
    assert actual is expected


def test_context_should_inherit_ownership_from_parent(step_context: Context, job_context: Context):
    # Assert
    actual = (
        step_context.maintainer,
        step_context.cost_center,
        step_context.owner,
        step_context.labels,
    )
    expected = (
        job_context.maintainer,
        job_context.cost_center,
        job_context.owner,
        job_context.labels,
    )
    assert actual == expected


def test_context_should_inherit_nominal_time_from_parent(
    step_context: Context, job_context: Context
):
    # Assert
    actual = step_context.nominal_time
    expected = job_context.nominal_time
    assert actual == expected


def test_context_should_have_own_identity_when_child(step_context: Context):
    # Assert
    actual = (
        step_context.id is not None,
        step_context.name,
        step_context.kind,
        step_context.plugin_kind,
    )
    expected = (True, "read_orders", "NoOpInput", "read")
    assert actual == expected


def test_context_should_have_own_run_id_when_child(step_context: Context, job_context: Context):
    # Assert
    assert step_context.run_id != job_context.run_id


def test_context_should_inherit_datetime_vars_from_parent(step_context: Context):
    # Assert
    actual = {
        "today": str(step_context.template_vars["today"]),
        "YYYY": step_context.template_vars["YYYY"],
        "MM": step_context.template_vars["MM"],
        "DD": step_context.template_vars["DD"],
        "ds": step_context.template_vars["ds"],
    }
    expected = {
        "today": "2026-01-15",
        "YYYY": "2026",
        "MM": "01",
        "DD": "15",
        "ds": "2026-01-15",
    }
    assert actual == expected


def test_context_child_temp_workdir_should_be_subdirectory_of_parent(
    step_context: Context, job_context: Context
):
    # Assert
    actual = (step_context.temp_workdir.parent, step_context.temp_workdir.name)
    expected = (job_context.temp_workdir, step_context.name)
    assert actual == expected


def test_context_without_parent_should_have_no_runner():
    # Act
    context = Context(
        name="standalone",
        kind="NoOpInput",
        plugin_kind="read",
        org="test",
        region="test",
        domain="test",
        layer="test",
        product="test",
        model="test",
        options={},
    )

    # Assert
    actual = context.runner
    expected = None
    assert actual == expected


# =============================================================================
# Testing Context - Factory Methods
# =============================================================================
def test_from_job_should_create_context_from_job_plugin():
    # Arrange
    job = MagicMock()
    job.name = "etl_orders"
    job.plugin_name = "LinearJob"
    job.plugin_kind = "job"
    job.org = "acme"
    job.region = "latam"
    job.domain = "sales"
    job.layer = "raw"
    job.product = "orders"
    job.model = "daily"
    job.options = {"retry": 3}
    job.maintainer = "team-data"
    job.cost_center = "cc-123"
    job.owner = "alice@acme.com"
    job.labels = {"env": "prod"}
    job.runner = MagicMock()

    # Act
    context = Context.from_job(job)

    # Assert
    actual = (
        context.name,
        context.kind,
        context.plugin_kind,
        context.org,
        context.maintainer,
        context.runner,
    )
    expected = (
        "etl_orders",
        "LinearJob",
        "job",
        "acme",
        "team-data",
        job.runner,
    )
    assert actual == expected


def test_from_step_should_create_context_from_step_plugin():
    # Arrange
    step = MagicMock()
    step.name = "read_orders"
    step.plugin_name = "NoOpInput"
    step.plugin_kind = "read"
    step.org = "acme"
    step.region = "latam"
    step.domain = "sales"
    step.layer = "raw"
    step.product = "orders"
    step.model = "daily"
    step.options = {"path": "/data/orders"}

    # Act
    context = Context.from_step(step)

    # Assert
    actual = (
        context.name,
        context.kind,
        context.plugin_kind,
        context.org,
    )
    expected = ("read_orders", "NoOpInput", "read", "acme")
    assert actual == expected


def test_from_step_should_link_to_parent_when_provided():
    # Arrange
    parent = Context(
        name="parent_job",
        kind="LinearJob",
        plugin_kind="job",
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="daily",
        options={},
        runner=MagicMock(),
    )
    step = MagicMock()
    step.name = "read_orders"
    step.plugin_name = "NoOpInput"
    step.plugin_kind = "read"
    step.org = "acme"
    step.region = "latam"
    step.domain = "sales"
    step.layer = "raw"
    step.product = "orders"
    step.model = "daily"
    step.options = {}

    # Act
    context = Context.from_step(step, parent=parent)

    # Assert
    actual = context.job
    expected = parent
    assert actual is expected


def test_as_step_context_should_create_child_context(job_context: Context):
    # Arrange
    step = MagicMock()
    step.name = "write_orders"
    step.plugin_name = "NoOpOutput"
    step.plugin_kind = "write"
    step.org = "acme"
    step.region = "latam"
    step.domain = "sales"
    step.layer = "raw"
    step.product = "orders"
    step.model = "daily"
    step.options = {}

    # Act
    context = job_context.as_step_context(step)

    # Assert
    actual = (context.name, context.kind, context.job)
    expected = ("write_orders", "NoOpOutput", job_context)
    assert actual == expected
