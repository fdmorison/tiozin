from tests.mocks.lineage.run_event import job_start_event as event
from tests.stubs import FailingLineageRegistryStub, LineageRegistryStub
from tiozin.api.context import Context
from tiozin.api.metadata.lineage.enums import EmitLevel

# =============================================================================
# Fire-and-forget contract
# =============================================================================


def test_proxy_should_silence_exception():
    # Act / Assert — must not raise
    registry = FailingLineageRegistryStub()
    registry.emit(event)


def test_proxy_should_return_none():
    # Arrange
    registry = FailingLineageRegistryStub()

    # Act
    result = registry.emit(event)

    # Assert
    actual = result
    expected = None
    assert actual == expected


def test_proxy_should_invoke_emit(job_context: Context):
    # Arrange
    registry = FailingLineageRegistryStub()

    # Act
    registry.emit(event)

    # Assert
    actual = registry.__wrapped__.emit_called
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


# =============================================================================
# Emit-level filtering in register()
# =============================================================================


def test_register_should_emit_when_level_is_job_and_context_is_job(job_context: Context):
    # Arrange
    registry = LineageRegistryStub(emit_level=EmitLevel.JOB)

    # Act
    registry.emit(event)

    # Assert
    actual = registry.__wrapped__.captured_event
    expected = event
    assert actual == expected


def test_register_should_skip_when_level_is_job_and_context_is_step(input_context: Context):
    # Arrange
    registry = LineageRegistryStub(emit_level=EmitLevel.JOB)

    # Act
    registry.emit(event)

    # Assert
    actual = registry.__wrapped__.captured_event
    expected = None
    assert actual == expected


def test_register_should_emit_when_level_is_step_and_context_is_step(input_context: Context):
    # Arrange
    registry = LineageRegistryStub(emit_level=EmitLevel.STEP)

    # Act
    registry.emit(event)

    # Assert
    actual = registry.__wrapped__.captured_event
    expected = event
    assert actual == expected


def test_register_should_skip_when_level_is_step_and_context_is_job(job_context: Context):
    # Arrange
    registry = LineageRegistryStub(emit_level=EmitLevel.STEP)

    # Act
    registry.emit(event)

    # Assert
    actual = registry.__wrapped__.captured_event
    expected = None
    assert actual == expected


def test_register_should_emit_when_level_is_all_and_context_is_job(job_context: Context):
    # Arrange
    registry = LineageRegistryStub(emit_level=EmitLevel.ALL)

    # Act
    registry.emit(event)

    # Assert
    actual = registry.__wrapped__.captured_event
    expected = event
    assert actual == expected


def test_register_should_emit_when_level_is_all_and_context_is_step(input_context: Context):
    # Arrange
    registry = LineageRegistryStub(emit_level=EmitLevel.ALL)

    # Act
    registry.emit(event)

    # Assert
    actual = registry.__wrapped__.captured_event
    expected = event
    assert actual == expected
