from unittest.mock import MagicMock

import pytest

from tiozin.api.context import Context
from tiozin.api.runtime.dataset import Dataset
from tiozin.api.runtime.runner_proxy import RunnerProxy
from tiozin.exceptions import AccessViolationError
from tiozin.family.tio_kernel import NoOpRunner


def test_proxy_should_forbid_setup_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(AccessViolationError):
        proxy.setup(None)


def test_proxy_should_forbid_teardown_access():
    # Arrange
    runner = NoOpRunner(name="test")
    proxy = RunnerProxy(runner)

    # Act/Assert
    with pytest.raises(AccessViolationError):
        proxy.teardown(None)


# =============================================================================
# Testing RunnerProxy.run — Dataset unwrapping
# =============================================================================


def test_run_should_unwrap_dataset_args_when_called_with_dataset(job_context: Context):
    # Arrange
    runner = MagicMock()
    runner.context = job_context
    proxy = RunnerProxy(runner)
    raw_plan = "SELECT 1"

    # Act
    proxy.run(Dataset(raw_plan))

    # Assert
    runner.run.assert_called_with(raw_plan)


def test_run_should_unwrap_dataset_result_when_runner_returns_dataset(job_context: Context):
    # Arrange
    runner = MagicMock()
    runner.context = job_context
    raw_result = "SELECT 1"
    runner.run.return_value = Dataset(raw_result)
    proxy = RunnerProxy(runner)

    # Act
    result = proxy.run()

    # Assert
    actual = result
    expected = raw_result
    assert actual == expected
