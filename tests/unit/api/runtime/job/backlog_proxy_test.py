from datetime import UTC, datetime

import pytest

from tests.stubs import BatchRegistryStub, JobStub
from tiozin import BacklogPolicy, Batch, BatchStatus, Context

_2026_01_15T01_00_00 = datetime(2026, 1, 15, 1, tzinfo=UTC)
_2026_01_15T02_00_00 = datetime(2026, 1, 15, 2, tzinfo=UTC)
_2026_01_15T03_00_00 = datetime(2026, 1, 15, 3, tzinfo=UTC)
_2026_01_15T04_00_00 = datetime(2026, 1, 15, 4, tzinfo=UTC)
_2026_01_15T05_00_00 = datetime(2026, 1, 15, 5, tzinfo=UTC)


@pytest.fixture(autouse=True)
def active_job_context(job_context: Context) -> Context:
    return job_context


# ============================================================================
# BacklogPolicy.NONE
# ============================================================================
def test_submit_should_run_the_job_once_when_policy_is_none(job_stub: JobStub):
    # Arrange
    job_stub.backlog = BacklogPolicy.NONE

    # Act
    result = job_stub.submit()

    # Assert
    actual = (job_stub.submit_count, result)
    expected = (1, ["result"])
    assert actual == expected


# ============================================================================
# BacklogPolicy.UPSTREAM and BacklogPolicy.MONOTONIC
# ============================================================================
@pytest.mark.parametrize("backlog", [BacklogPolicy.UPSTREAM, BacklogPolicy.MONOTONIC])
def test_submit_should_process_the_entire_backlog(
    backlog,
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    backlog = [
        Batch(**fake_domain, nominal_time=_2026_01_15T01_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T02_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T03_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T04_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T05_00_00),
    ]
    batch_registry_stub.backlog = backlog
    job_stub.backlog = backlog
    job_stub.max_batches_per_run = 2

    # Act
    job_stub.submit()

    # Assert
    actual = [batch.status for batch in backlog]
    expected = [
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
    ]
    assert actual == expected


@pytest.mark.parametrize("backlog", [BacklogPolicy.UPSTREAM, BacklogPolicy.MONOTONIC])
def test_submit_should_expose_only_the_current_chunk_to_each_run(
    backlog,
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    backlog = [
        batch_1 := Batch(**fake_domain, nominal_time=_2026_01_15T01_00_00),
        batch_2 := Batch(**fake_domain, nominal_time=_2026_01_15T02_00_00),
        batch_3 := Batch(**fake_domain, nominal_time=_2026_01_15T03_00_00),
        batch_4 := Batch(**fake_domain, nominal_time=_2026_01_15T04_00_00),
        batch_5 := Batch(**fake_domain, nominal_time=_2026_01_15T05_00_00),
    ]
    batch_registry_stub.backlog = backlog
    job_stub.backlog = backlog
    job_stub.max_batches_per_run = 2

    # Act
    job_stub.submit()

    # Assert
    actual = job_stub.captured_backlogs
    expected = [
        [batch_1, batch_2],
        [batch_3, batch_4],
        [batch_5],
    ]
    assert actual == expected


@pytest.mark.parametrize("backlog", [BacklogPolicy.UPSTREAM, BacklogPolicy.MONOTONIC])
def test_submit_should_skip_when_backlog_is_empty(
    backlog,
    job_stub: JobStub,
):
    # Arrange
    job_stub.backlog = backlog

    # Act
    result = job_stub.submit()

    # Assert
    actual = (job_stub.submit_count, result)
    expected = (0, [])
    assert actual == expected


@pytest.mark.parametrize("backlog", [BacklogPolicy.UPSTREAM, BacklogPolicy.MONOTONIC])
def test_submit_should_rollback_the_backlog_when_execution_fails_within_retries(
    backlog,
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    backlog = [
        Batch(**fake_domain, nominal_time=_2026_01_15T01_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T02_00_00),
    ]
    batch_registry_stub.backlog = backlog
    job_stub.backlog = backlog
    job_stub.max_batches_per_run = 2
    job_stub.failure = RuntimeError("boom")

    # Act
    with pytest.raises(RuntimeError):
        job_stub.submit()

    # Assert
    actual = [batch.status for batch in backlog]
    expected = [
        BatchStatus.FAILED,
        BatchStatus.FAILED,
    ]
    assert actual == expected


@pytest.mark.parametrize(
    "backlog",
    [BacklogPolicy.UPSTREAM, BacklogPolicy.MONOTONIC],
)
def test_submit_should_quarantine_the_backlog_when_execution_fails_beyond_retries(
    backlog,
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    backlog = [
        Batch(**fake_domain, nominal_time=_2026_01_15T01_00_00, attempts=3),
        Batch(**fake_domain, nominal_time=_2026_01_15T02_00_00, attempts=3),
    ]
    batch_registry_stub.backlog = backlog
    job_stub.backlog = backlog
    job_stub.max_batches_per_run = 2
    job_stub.failure = RuntimeError("boom")

    # Act
    with pytest.raises(RuntimeError):
        job_stub.submit()

    # Assert
    actual = [batch.status for batch in backlog]
    expected = [
        BatchStatus.QUARANTINED,
        BatchStatus.QUARANTINED,
    ]
    assert actual == expected
