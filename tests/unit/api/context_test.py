import pendulum
import pytest

from tiozin.api.processors.context import Context


# ============================================================================
# Testing Context - Identity Fields
# ============================================================================
def test_context_should_require_identity_fields():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={"key": "value"},
    )

    # Assert
    actual = (
        context.id,
        context.name,
        context.kind,
        context.plugin_kind,
        context.options,
    )
    expected = (
        "ctx-123",
        "test_context",
        "TestKind",
        "TestPlugin",
        {"key": "value"},
    )
    assert actual == expected


def test_context_should_generate_run_id_automatically():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )

    # Assert
    assert context.run_id is not None
    assert len(context.run_id) > 0


# ============================================================================
# Testing Context - Template Variables
# ============================================================================
def test_context_should_include_identity_fields_in_template_vars():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={"key": "value"},
    )

    # Assert
    actual = (
        context.template_vars["id"],
        context.template_vars["name"],
        context.template_vars["kind"],
        context.template_vars["plugin_kind"],
    )
    expected = ("ctx-123", "test_context", "TestKind", "TestPlugin")
    assert actual == expected


def test_context_should_exclude_session_from_template_vars():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
        session={"secret": "data"},
    )

    # Assert
    assert "session" not in context.template_vars


def test_context_should_merge_custom_template_vars():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
        template_vars={"custom_var": "custom_value"},
    )

    # Assert
    actual = (
        context.template_vars["custom_var"],
        context.template_vars["id"],
    )
    expected = ("custom_value", "ctx-123")
    assert actual == expected


def test_context_template_vars_should_be_immutable():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )

    # Assert
    with pytest.raises(TypeError):
        context.template_vars["new_key"] = "value"


# ============================================================================
# Testing Context - Runtime Timestamps
# ============================================================================
def test_context_should_have_null_timestamps_by_default():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )

    # Assert
    actual = (
        context.setup_at,
        context.executed_at,
        context.teardown_at,
        context.finished_at,
    )
    expected = (None, None, None, None)
    assert actual == expected


# ============================================================================
# Testing Context - Timing Helpers
# ============================================================================
def test_context_delay_should_calculate_total_duration():
    # Arrange
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )
    context.setup_at = pendulum.parse("2026-01-15T10:00:00+00:00")
    context.finished_at = pendulum.parse("2026-01-15T10:00:05+00:00")

    # Act
    actual = context.delay

    # Assert
    expected = 5.0
    assert actual == expected


def test_context_setup_delay_should_calculate_setup_duration():
    # Arrange
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )
    context.setup_at = pendulum.parse("2026-01-15T10:00:00+00:00")
    context.executed_at = pendulum.parse("2026-01-15T10:00:02+00:00")

    # Act
    actual = context.setup_delay

    # Assert
    expected = 2.0
    assert actual == expected


def test_context_execution_delay_should_calculate_execution_duration():
    # Arrange
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )
    context.executed_at = pendulum.parse("2026-01-15T10:00:02+00:00")
    context.teardown_at = pendulum.parse("2026-01-15T10:00:10+00:00")

    # Act
    actual = context.execution_delay

    # Assert
    expected = 8.0
    assert actual == expected


def test_context_teardown_delay_should_calculate_teardown_duration():
    # Arrange
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )
    context.teardown_at = pendulum.parse("2026-01-15T10:00:10+00:00")
    context.finished_at = pendulum.parse("2026-01-15T10:00:11+00:00")

    # Act
    actual = context.teardown_delay

    # Assert
    expected = 1.0
    assert actual == expected


# ============================================================================
# Testing Context - Temporary Storage
# ============================================================================
def test_context_should_create_temp_workdir_automatically():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )

    # Assert
    assert context.temp_workdir is not None
    assert context.temp_workdir.exists()
    assert context.temp_workdir.is_dir()


def test_context_temp_workdir_should_be_organized_by_name_and_run_id():
    # Act
    context = Context(
        id="ctx-123",
        name="my_job",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )

    # Assert
    # temp_workdir should be: /tmp/tiozin/<name>/<run_id>
    assert "/tiozin/" in str(context.temp_workdir)
    assert "/my_job/" in str(context.temp_workdir)
    assert f"/{context.run_id}" in str(context.temp_workdir)


def test_context_temp_workdir_should_be_available_in_template_vars():
    # Act
    context = Context(
        id="ctx-123",
        name="test_context",
        kind="TestKind",
        plugin_kind="TestPlugin",
        options={},
    )

    # Assert
    actual = context.template_vars.get("temp_workdir")
    expected = context.temp_workdir
    assert actual is expected
