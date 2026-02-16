import pytest

from tests.stubs.runner import RunnerStub


def test_runner_should_default_streaming_to_false():
    """Runner instances are non-streaming by default."""
    # Act
    runner = RunnerStub(name="stub")

    # Assert
    actual = runner.streaming
    expected = False
    assert actual == expected


@pytest.mark.parametrize("streaming", [True, False])
def test_runner_should_accept_streaming_parameter(streaming: bool):
    """Runner respects the streaming flag passed at construction."""
    # Act
    runner = RunnerStub(name="stub", streaming=streaming)

    # Assert
    actual = runner.streaming
    expected = streaming
    assert actual == expected


def test_runner_should_expose_session_property():
    """Runner exposes a session property for the active execution session."""
    # Act
    runner = RunnerStub(name="stub")

    # Assert
    actual = runner.session
    expected = {}
    assert actual == expected
