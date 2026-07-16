from datetime import UTC, datetime

import pytest

from tests.stubs import BatchRegistryStub, JobStub
from tiozin import Batch, BatchSourcePolicy, BatchStatus, Context


@pytest.fixture(autouse=True)
def active_job_context(job_context: Context) -> Context:
    return job_context


# ============================================================================
# BatchSourcePolicy.NONE
# ============================================================================
def test_submit_should_run_the_job_once_when_policy_is_none(job_stub: JobStub):
    # Arrange
    job_stub.batch_source = BatchSourcePolicy.NONE

    # Act
    result = job_stub.submit()

    # Assert
    actual = (job_stub.submit_count, result)
    expected = (1, ["result"])
    assert actual == expected


# ============================================================================
# BatchSourcePolicy.UPSTREAM and BatchSourcePolicy.SELF
# ============================================================================
@pytest.mark.parametrize("batch_source", [BatchSourcePolicy.UPSTREAM, BatchSourcePolicy.SELF])
def test_submit_should_process_the_entire_backlog(
    batch_source,
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    batch_registry_stub.backlog = [
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 1, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 2, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 3, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 4, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 5, tzinfo=UTC)),
    ]
    job_stub.batch_source = batch_source
    job_stub.max_batches_per_run = 2

    # Act
    job_stub.submit()

    # Assert
    actual = job_stub.submit_count
    expected = 3
    assert actual == expected


@pytest.mark.parametrize("batch_source", [BatchSourcePolicy.UPSTREAM, BatchSourcePolicy.SELF])
def test_submit_should_mark_the_backlog_as_succeeded(
    batch_source,
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    batch_registry_stub.backlog = [
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 1, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 2, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 3, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 4, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 5, tzinfo=UTC)),
    ]
    job_stub.batch_source = batch_source
    job_stub.max_batches_per_run = 2

    # Act
    job_stub.submit()

    # Assert
    actual = [batch.status for batch in batch_registry_stub.backlog]
    expected = [
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
    ]
    assert actual == expected


@pytest.mark.parametrize("batch_source", [BatchSourcePolicy.UPSTREAM, BatchSourcePolicy.SELF])
def test_submit_should_skip_when_backlog_is_empty(
    batch_source,
    job_stub: JobStub,
):
    # Arrange
    job_stub.batch_source = batch_source

    # Act
    result = job_stub.submit()

    # Assert
    actual = (job_stub.submit_count, result)
    expected = (0, [])
    assert actual == expected


@pytest.mark.parametrize("batch_source", [BatchSourcePolicy.UPSTREAM, BatchSourcePolicy.SELF])
def test_submit_should_mark_the_backlog_as_failed_when_execution_fails(
    batch_source,
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    batch_registry_stub.backlog = [
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 1, tzinfo=UTC)),
        Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, 2, tzinfo=UTC)),
    ]
    job_stub.batch_source = batch_source
    job_stub.max_batches_per_run = 2
    job_stub.failure = RuntimeError("boom")

    # Act
    with pytest.raises(RuntimeError):
        job_stub.submit()

    # Assert
    actual = [batch.status for batch in batch_registry_stub.backlog]
    expected = [
        BatchStatus.FAILED,
        BatchStatus.FAILED,
    ]
    assert actual == expected
