import pytest

from tests.stubs.runner import StubRunner


def test_runner_should_default_streaming_to_false():
    """Runner instances are non-streaming by default."""
    # Act
    runner = StubRunner(name="stub")

    # Assert
    actual = runner.streaming
    expected = False
    assert actual == expected


@pytest.mark.parametrize("streaming", [True, False])
def test_runner_should_accept_streaming_parameter(streaming: bool):
    """Runner respects the streaming flag passed at construction."""
    # Act
    runner = StubRunner(name="stub", streaming=streaming)

    # Assert
    actual = runner.streaming
    expected = streaming
    assert actual == expected
