from unittest.mock import MagicMock

import pytest

from tiozin.api import JobContext, StepContext


@pytest.fixture
def job_context() -> MagicMock:
    mock = MagicMock(spec=JobContext)
    mock.id = "job-123"
    mock.run_id = "job-run-abc"
    mock.session = {"shared": "data"}
    mock.template_vars = {
        "today": "2026-01-15",
        "YYYY": "2026",
        "D": {0: "2026-01-15"},
    }
    return mock


@pytest.fixture
def step_context(job_context: MagicMock) -> StepContext:
    return StepContext(
        id="step-456",
        name="read_orders",
        kind="NoOpInput",
        plugin_kind="read",
        options={"path": "/data/orders"},
        job=job_context,
        org="acme",
        region="latam",
        domain="sales",
        layer="raw",
        product="orders",
        model="daily",
        template_vars=job_context.template_vars,
        session=job_context.session,
    )


# ============================================================================
# Testing StepContext - Parent Job Reference
# ============================================================================
def test_step_context_should_have_reference_to_parent_job(step_context: StepContext):
    # Assert
    actual = step_context.job.id
    expected = "job-123"
    assert actual == expected


def test_step_context_should_inherit_session_from_job(
    job_context: MagicMock, step_context: StepContext
):
    # Assert
    assert step_context.session is job_context.session


# ============================================================================
# Testing StepContext - Fundamentals
# ============================================================================
def test_step_context_should_have_fundamentals(step_context: StepContext):
    # Assert
    actual = (
        step_context.org,
        step_context.region,
        step_context.domain,
        step_context.layer,
        step_context.product,
        step_context.model,
    )
    expected = ("acme", "latam", "sales", "raw", "orders", "daily")
    assert actual == expected


# ============================================================================
# Testing StepContext - Template Variables
# ============================================================================
def test_step_context_should_include_step_fields_in_template_vars(step_context: StepContext):
    # Assert
    actual = (
        step_context.template_vars["id"],
        step_context.template_vars["name"],
        step_context.template_vars["kind"],
        step_context.template_vars["org"],
        step_context.template_vars["domain"],
    )
    expected = ("step-456", "read_orders", "NoOpInput", "acme", "sales")
    assert actual == expected


def test_step_context_should_inherit_datetime_vars_from_job(step_context: StepContext):
    # Assert
    actual = (
        step_context.template_vars["today"],
        step_context.template_vars["YYYY"],
        step_context.template_vars["D"][0],
    )
    expected = ("2026-01-15", "2026", "2026-01-15")
    assert actual == expected


# ============================================================================
# Testing StepContext - Identity
# ============================================================================
def test_step_context_should_have_own_identity(step_context: StepContext):
    # Assert
    actual = (
        step_context.id,
        step_context.name,
        step_context.kind,
        step_context.plugin_kind,
    )
    expected = ("step-456", "read_orders", "NoOpInput", "read")
    assert actual == expected


def test_step_context_should_have_own_run_id(step_context: StepContext, job_context: MagicMock):
    # Assert
    assert step_context.run_id != job_context.run_id
