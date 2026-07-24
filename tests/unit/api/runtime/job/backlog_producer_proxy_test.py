from datetime import UTC, datetime

from tests.stubs import BatchRegistryStub, JobStub
from tiozin import Batch, BatchStatus, Context
from tiozin.api.runtime.job.backlog_producer_proxy import BacklogProducerJobProxy

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

FRONTIER_END = datetime(2010, 1, 15, 10, 0, tzinfo=UTC)


def test_resolve_batch_should_create_first_batch_since_1970(
    job_context: Context, job_stub: JobStub, fake_domain: dict
):
    # Arrange
    proxy = BacklogProducerJobProxy(job_stub)

    # Act
    batch = proxy.resolve_batch(job_stub)

    # Assert
    actual = (
        batch.nominal_start_time,
        batch.nominal_end_time,
    )
    expected = (
        EPOCH,
        job_context.nominal_time,
    )
    assert actual == expected


def test_resolve_batch_should_create_subsequent_batches_since_frontier_end(
    job_context: Context,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
    fake_domain: dict,
):
    # Arrange
    frontier = Batch(
        **fake_domain,
        nominal_time=FRONTIER_END,
        nominal_end_time=FRONTIER_END,
        status=BatchStatus.SUCCEEDED,
    )
    batch_registry_stub.get_frontier = lambda **_: frontier
    proxy = BacklogProducerJobProxy(job_stub)

    # Act
    batch = proxy.resolve_batch(job_stub)

    # Assert
    actual = (
        batch.nominal_start_time,
        batch.nominal_end_time,
    )
    expected = (
        FRONTIER_END,
        job_context.nominal_time,
    )
    assert actual == expected


def test_resolve_batch_should_preserve_frontier_bookmarks(
    job_context: Context,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
    fake_domain: dict,
):
    # Arrange
    frontier = Batch(
        **fake_domain,
        nominal_time=FRONTIER_END,
        status=BatchStatus.SUCCEEDED,
        bookmarks={"orders": 42},
    )
    batch_registry_stub.get_frontier = lambda **_: frontier
    proxy = BacklogProducerJobProxy(job_stub)

    # Act
    batch = proxy.resolve_batch(job_stub)

    # Assert
    actual = batch.bookmarks
    expected = {"orders": 42}
    assert actual == expected


# ============================================================================
# operational frontier: resume
# ============================================================================
def test_resolve_batch_should_resume_frontier(
    job_context: Context,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
    fake_domain: dict,
):
    # Arrange
    frontier = Batch(
        **fake_domain,
        nominal_time=FRONTIER_END,
        status=BatchStatus.RUNNING,
    )
    batch_registry_stub.get_frontier = lambda **_: frontier
    proxy = BacklogProducerJobProxy(job_stub)

    # Act
    batch = proxy.resolve_batch(job_stub)

    # Assert
    assert batch is frontier


def test_resolve_batch_should_extend_frontier_window_on_resume(
    job_context: Context,
    job_stub: JobStub,
    batch_registry_stub: BatchRegistryStub,
    fake_domain: dict,
):
    # Arrange
    frontier = Batch(
        **fake_domain,
        nominal_time=FRONTIER_END,
        nominal_end_time=FRONTIER_END,
        status=BatchStatus.RUNNING,
    )
    batch_registry_stub.get_frontier = lambda **_: frontier
    proxy = BacklogProducerJobProxy(job_stub)

    # Act
    proxy.resolve_batch(job_stub)

    # Assert
    actual = frontier.nominal_end_time
    expected = job_context.nominal_time
    assert actual == expected
