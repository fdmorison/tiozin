from unittest.mock import MagicMock

import pytest

from tiozin.api import JobContext, RunnerContext


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
def runner_context(job_context: MagicMock) -> RunnerContext:
    return RunnerContext(
        id="runner-789",
        name="noop_runner",
        kind="NoOpRunner",
        plugin_kind="run",
        options={"streaming": False},
        job=job_context,
        template_vars=job_context.template_vars,
        session=job_context.session,
    )


# ============================================================================
# Testing RunnerContext - Parent Job Reference
# ============================================================================
def test_runner_context_should_have_reference_to_parent_job(runner_context: RunnerContext):
    # Assert
    actual = runner_context.job.id
    expected = "job-123"
    assert actual == expected


def test_runner_context_should_inherit_session_from_job(
    job_context: MagicMock, runner_context: RunnerContext
):
    # Assert
    assert runner_context.session is job_context.session


# ============================================================================
# Testing RunnerContext - Template Variables
# ============================================================================
def test_runner_context_should_include_runner_fields_in_template_vars(
    runner_context: RunnerContext,
):
    # Assert
    actual = (
        runner_context.template_vars["id"],
        runner_context.template_vars["name"],
        runner_context.template_vars["kind"],
    )
    expected = ("runner-789", "noop_runner", "NoOpRunner")
    assert actual == expected


def test_runner_context_should_inherit_datetime_vars_from_job(runner_context: RunnerContext):
    # Assert
    actual = (
        runner_context.template_vars["today"],
        runner_context.template_vars["YYYY"],
        runner_context.template_vars["D"][0],
    )
    expected = ("2026-01-15", "2026", "2026-01-15")
    assert actual == expected


# ============================================================================
# Testing RunnerContext - Identity
# ============================================================================
def test_runner_context_should_have_own_identity(runner_context: RunnerContext):
    # Assert
    actual = (
        runner_context.id,
        runner_context.name,
        runner_context.kind,
        runner_context.plugin_kind,
    )
    expected = ("runner-789", "noop_runner", "NoOpRunner", "run")
    assert actual == expected


def test_runner_context_should_have_own_run_id(
    runner_context: RunnerContext, job_context: MagicMock
):
    # Assert
    assert runner_context.run_id != job_context.run_id
