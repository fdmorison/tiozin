from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from tests.stubs import BatchRegistryStub, JobStub
from tiozin import Batch, BatchStatus, Context
from tiozin.api.runtime.job.backlog_consumer_proxy import BacklogConsumerJobProxy
from tiozin.exceptions import JobRuntimeError

_2026_01_15T01_00_00 = datetime(2026, 1, 15, 1, tzinfo=UTC)
_2026_01_15T02_00_00 = datetime(2026, 1, 15, 2, tzinfo=UTC)
_2026_01_15T03_00_00 = datetime(2026, 1, 15, 3, tzinfo=UTC)
_2026_01_15T04_00_00 = datetime(2026, 1, 15, 4, tzinfo=UTC)
_2026_01_15T05_00_00 = datetime(2026, 1, 15, 5, tzinfo=UTC)

CONSUMING_POLICY = MagicMock(consumes_backlog=True)
NON_CONSUMING_POLICY = MagicMock(consumes_backlog=False)


@pytest.fixture(autouse=True)
def active_job_context(job_context: Context) -> Context:
    return job_context


# ============================================================================
# Jobs that do not consume backlog
# ============================================================================
def test_submit_should_run_the_job_once_when_backlog_is_not_consumed(job_stub: JobStub):
    # Arrange
    job_stub.backlog_policy = NON_CONSUMING_POLICY

    # Act
    result = BacklogConsumerJobProxy(job_stub).submit()

    # Assert
    actual = (job_stub.submit_count, result)
    expected = (1, ["result"])
    assert actual == expected


# ============================================================================
# Jobs that consume backlog
# ============================================================================
def test_submit_should_process_the_entire_backlog(
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
    job_stub.backlog_policy = CONSUMING_POLICY
    job_stub.max_batches_per_run = 2

    # Act
    BacklogConsumerJobProxy(job_stub).submit()

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


def test_submit_should_expose_only_the_current_chunk_to_each_run(
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
    job_stub.backlog_policy = CONSUMING_POLICY
    job_stub.max_batches_per_run = 2

    # Act
    BacklogConsumerJobProxy(job_stub).submit()

    # Assert
    actual = job_stub.captured_backlogs
    expected = [
        [batch_1, batch_2],
        [batch_3, batch_4],
        [batch_5],
    ]
    assert actual == expected


def test_submit_should_skip_when_backlog_is_empty(job_stub: JobStub):
    # Arrange
    job_stub.backlog_policy = CONSUMING_POLICY

    # Act
    result = BacklogConsumerJobProxy(job_stub).submit()

    # Assert
    actual = (job_stub.submit_count, result)
    expected = (0, [])
    assert actual == expected


def test_submit_should_rollback_the_backlog_when_execution_fails_within_retries(
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
    job_stub.backlog_policy = CONSUMING_POLICY
    job_stub.max_batches_per_run = 2
    job_stub.failure = RuntimeError("boom")

    # Act
    with pytest.raises(JobRuntimeError):
        BacklogConsumerJobProxy(job_stub).submit()

    # Assert
    actual = [batch.status for batch in backlog]
    expected = [
        BatchStatus.FAILED,
        BatchStatus.FAILED,
    ]
    assert actual == expected


def test_submit_should_quarantine_the_backlog_when_execution_fails_beyond_retries(
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
    job_stub.backlog_policy = CONSUMING_POLICY
    job_stub.max_batches_per_run = 2
    job_stub.failure = RuntimeError("boom")

    # Act
    with pytest.raises(JobRuntimeError):
        BacklogConsumerJobProxy(job_stub).submit()

    # Assert
    actual = [batch.status for batch in backlog]
    expected = [
        BatchStatus.QUARANTINED,
        BatchStatus.QUARANTINED,
    ]
    assert actual == expected


def test_submit_should_not_stop_on_the_first_failed_slice(
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
    job_stub.backlog_policy = CONSUMING_POLICY
    job_stub.max_batches_per_run = 2
    job_stub.submit = MagicMock(side_effect=[RuntimeError("boom"), "result", "result"])

    # Act
    with pytest.raises(JobRuntimeError):
        BacklogConsumerJobProxy(job_stub).submit()

    # Assert
    actual = [batch.status for batch in backlog]
    expected = [
        BatchStatus.FAILED,
        BatchStatus.FAILED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
        BatchStatus.SUCCEEDED,
    ]
    assert actual == expected


def test_submit_should_raise_runtime_error_when_a_slice_fails(
    fake_domain: dict,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
):
    # Arrange
    batch_registry_stub.backlog = [
        Batch(**fake_domain, nominal_time=_2026_01_15T01_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T02_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T03_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T04_00_00),
        Batch(**fake_domain, nominal_time=_2026_01_15T05_00_00),
    ]
    job_stub.backlog_policy = CONSUMING_POLICY
    job_stub.max_batches_per_run = 2
    job_stub.submit = MagicMock(side_effect=[RuntimeError("boom"), "result", "result"])

    # Act
    with pytest.raises(JobRuntimeError) as error:
        BacklogConsumerJobProxy(job_stub).submit()

    # Assert
    actual = str(error.value)
    expected = "The job failed to process 2 of 5 batches."
    assert actual == expected
