"""
LineageRegistryProxy — fire-and-forget contract.

All LineageRegistry instances are automatically wrapped via @tioproxy.
Calling register() on a stub already goes through the proxy.
"""

from tests.mocks.lineage.run_event import job_start_event as event
from tests.stubs import FailingLineageRegistryStub, LineageRegistryStub


def test_proxy_should_silence_exception():
    # Act / Assert — must not raise
    registry = FailingLineageRegistryStub()
    registry.register(event.run_id, event)


def test_proxy_should_return_none():
    # Arrange
    registry = FailingLineageRegistryStub()

    # Act
    result = registry.register(event.run_id, event)

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_proxy_should_invoke_register():
    # Arrange
    registry = FailingLineageRegistryStub()

    # Act
    registry.register(event.run_id, event)

    # Assert
    actual = registry.__wrapped__.register_called
    expected = True
    assert actual == expected


def test_proxy_should_pass_through_attribute_access():
    # Arrange
    registry = LineageRegistryStub()

    # Act
    result = registry.location

    # Assert
    actual = result
    expected = "stub://lineage"
    assert actual == expected
