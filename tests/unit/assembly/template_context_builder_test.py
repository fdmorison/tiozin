from dataclasses import dataclass, field
from datetime import datetime

import pytest

from tiozin.assembly.template_context_builder import TemplateContextBuilder
from tiozin.utils.relative_date import RelativeDate


# ============================================================================
# Testing TemplateContextBuilder - Basic Build
# ============================================================================
def test_builder_should_build_immutable_context():
    # Act
    context = TemplateContextBuilder().build()

    # Assert
    with pytest.raises(TypeError):
        context["new_key"] = "value"


def test_builder_should_include_day_in_context():
    # Arrange
    builder = TemplateContextBuilder().with_datetime()

    # Act
    context = builder.build()

    # Assert
    actual = (
        "DAY" in context,
        isinstance(context["DAY"], RelativeDate),
    )
    expected = (True, True)
    assert actual == expected


def test_builder_should_include_relative_date_properties_in_context():
    # Arrange
    builder = TemplateContextBuilder().with_datetime()

    # Act
    context = builder.build()

    # Assert
    expected = {"ds", "ts", "iso", "YYYY", "MM", "DD"}
    actual = {k for k in expected if k in context}
    assert actual == expected


# ============================================================================
# Testing TemplateContextBuilder - with_datetime (typo: with_datetime)
# ============================================================================
def test_builder_should_set_custom_datetime_when_with_datetime_called():
    # Arrange
    custom_dt = datetime(2025, 6, 15, 12, 30, 45)

    # Act
    context = TemplateContextBuilder().with_datetime(custom_dt).build()

    # Assert
    actual = {
        "ds": context["ds"],
        "YYYY": context["YYYY"],
        "MM": context["MM"],
        "DD": context["DD"],
    }
    expected = {
        "ds": "2025-06-15",
        "YYYY": "2025",
        "MM": "06",
        "DD": "15",
    }
    assert actual == expected


def test_builder_should_raise_when_with_datetime_receives_invalid_type():
    # Act & Assert
    with pytest.raises(TypeError, match="nominal_date must be a datetime"):
        TemplateContextBuilder().with_datetime("2025-06-15")


def test_builder_should_affect_day_object_when_with_datetime_called():
    # Arrange
    custom_dt = datetime(2025, 6, 15, 12, 30, 45)

    # Act
    context = TemplateContextBuilder().with_datetime(custom_dt).build()
    day = context["DAY"]

    # Assert
    actual = (
        day.date,
        day.yesterday.date,
        day.tomorrow.date,
    )
    expected = (
        "2025-06-15",
        "2025-06-14",
        "2025-06-16",
    )
    assert actual == expected


# ============================================================================
# Testing TemplateContextBuilder - with_defaults
# ============================================================================
def test_builder_should_add_default_values_when_with_defaults_called():
    # Act
    context = (
        TemplateContextBuilder().with_defaults({"env": "production", "region": "us-east"}).build()
    )

    # Assert
    expected = {"env": "production", "region": "us-east"}
    actual = {k: context.get(k) for k in expected}
    assert actual == expected


def test_builder_should_override_defaults_when_variables_provided():
    # Act
    context = (
        TemplateContextBuilder()
        .with_defaults({"env": "default"})
        .with_variables({"env": "override"})
        .build()
    )

    # Assert
    actual = context["env"]
    expected = "override"
    assert actual == expected


def test_builder_should_raise_when_with_defaults_receives_invalid_type():
    # Act & Assert
    with pytest.raises(TypeError, match="defaults must be a mapping"):
        TemplateContextBuilder().with_defaults("not a mapping")


def test_builder_should_merge_defaults_when_with_defaults_called_multiple_times():
    # Act
    context = TemplateContextBuilder().with_defaults({"a": 1}).with_defaults({"b": 2}).build()

    # Assert
    expected = {"a": 1, "b": 2}
    actual = {k: context.get(k) for k in expected}
    assert actual == expected


# ============================================================================
# Testing TemplateContextBuilder - with_variables
# ============================================================================
def test_builder_should_add_variables_when_with_variables_called():
    # Act
    context = (
        TemplateContextBuilder().with_variables({"domain": "sales", "table": "orders"}).build()
    )

    # Assert
    expected = {"domain": "sales", "table": "orders"}
    actual = {k: context.get(k) for k in expected}
    assert actual == expected


def test_builder_should_raise_when_with_variables_receives_invalid_type():
    # Act & Assert
    with pytest.raises(TypeError, match="vars must be a mapping"):
        TemplateContextBuilder().with_variables(["not", "a", "mapping"])


def test_builder_should_merge_variables_when_with_variables_called_multiple_times():
    # Act
    context = TemplateContextBuilder().with_variables({"x": 1}).with_variables({"y": 2}).build()

    # Assert
    expected = {"x": 1, "y": 2}
    actual = {k: context.get(k) for k in expected}
    assert actual == expected


def test_builder_should_override_variable_when_with_variables_called_with_same_key():
    # Act
    context = (
        TemplateContextBuilder()
        .with_variables({"key": "first"})
        .with_variables({"key": "second"})
        .build()
    )

    # Assert
    actual = context["key"]
    expected = "second"
    assert actual == expected


# ============================================================================
# Testing TemplateContextBuilder - with_context (dataclass)
# ============================================================================
@dataclass
class SampleContext:
    name: str
    value: int
    secret: str = field(metadata={"template": False})


@dataclass
class ContextWithoutMetadata:
    name: str
    value: int


def test_builder_should_add_dataclass_fields_when_with_context_called():
    # Arrange
    ctx = SampleContext(name="test", value=42, secret="hidden")

    # Act
    context = TemplateContextBuilder().with_context(ctx).build()

    # Assert
    expected = {"name": "test", "value": 42}
    actual = {k: context.get(k) for k in expected}
    assert actual == expected


def test_builder_should_exclude_fields_with_template_false_when_with_context_called():
    # Arrange
    ctx = SampleContext(name="test", value=42, secret="hidden")

    # Act
    context = TemplateContextBuilder().with_context(ctx).build()

    # Assert
    actual = "secret" in context
    expected = False
    assert actual == expected


def test_builder_should_include_fields_without_metadata_when_with_context_called():
    # Arrange
    ctx = ContextWithoutMetadata(name="test", value=42)

    # Act
    context = TemplateContextBuilder().with_context(ctx).build()

    # Assert
    expected = {"name": "test", "value": 42}
    actual = {k: context.get(k) for k in expected}
    assert actual == expected


def test_builder_should_raise_when_with_context_receives_non_dataclass():
    # Act & Assert
    with pytest.raises(TypeError, match="context must be a dataclass instance"):
        TemplateContextBuilder().with_context({"not": "dataclass"})


# ============================================================================
# Testing TemplateContextBuilder - Precedence
# ============================================================================
def test_builder_should_override_defaults_with_variables():
    # Act
    context = (
        TemplateContextBuilder()
        .with_defaults({"key": "default"})
        .with_variables({"key": "variable"})
        .build()
    )

    # Assert
    actual = context["key"]
    expected = "variable"
    assert actual == expected


def test_builder_should_override_variables_with_context():
    # Arrange
    @dataclass
    class Ctx:
        key: str

    ctx = Ctx(key="from_context")

    # Act
    context = (
        TemplateContextBuilder().with_variables({"key": "from_variable"}).with_context(ctx).build()
    )

    # Assert
    actual = context["key"]
    expected = "from_context"
    assert actual == expected


def test_builder_should_override_all_with_date_properties():
    # Act
    context = (
        TemplateContextBuilder()
        .with_datetime()
        .with_defaults({"ds": "default_ds"})
        .with_variables({"ds": "variable_ds"})
        .build()
    )

    # Assert - ds from RelativeDate.to_dict() should override
    actual = (
        context["ds"] != "default_ds",
        context["ds"] != "variable_ds",
    )
    expected = (True, True)
    assert actual == expected


# ============================================================================
# Testing TemplateContextBuilder - DAY Navigation
# ============================================================================
def test_builder_should_support_day_navigation_with_index():
    # Arrange
    custom_dt = datetime(2026, 1, 17, 10, 30, 45)

    # Act
    context = TemplateContextBuilder().with_datetime(custom_dt).build()
    day = context["DAY"]

    # Assert
    actual = (
        day[-1].date,
        day[0].date,
        day[7].date,
    )
    expected = (
        "2026-01-16",
        "2026-01-17",
        "2026-01-24",
    )
    assert actual == expected


def test_builder_should_support_day_navigation_with_properties():
    # Arrange
    custom_dt = datetime(2026, 1, 17, 10, 30, 45)

    # Act
    context = TemplateContextBuilder().with_datetime(custom_dt).build()
    day = context["DAY"]

    # Assert
    actual = (
        day.yesterday.date,
        day.tomorrow.date,
    )
    expected = (
        "2026-01-16",
        "2026-01-18",
    )
    assert actual == expected


def test_builder_should_support_day_fs_navigation():
    # Arrange
    custom_dt = datetime(2026, 1, 17, 10, 30, 45)

    # Act
    context = TemplateContextBuilder().with_datetime(custom_dt).build()
    day = context["DAY"]

    # Assert
    actual = (
        day.fs.date,
        day[-1].fs.date,
    )
    expected = (
        "2026-01-17",
        "2026-01-16",
    )
    assert actual == expected


def test_builder_should_support_day_fsdeep_navigation():
    # Arrange
    custom_dt = datetime(2026, 1, 17, 10, 30, 45)

    # Act
    context = TemplateContextBuilder().with_datetime(custom_dt).build()
    day = context["DAY"]

    # Assert
    actual = (
        day.fsdeep.day,
        day[-1].fsdeep.hour,
    )
    expected = (
        "year=2026/month=01/day=17",
        "year=2026/month=01/day=16/hour=10",
    )
    assert actual == expected


# ============================================================================
# Testing TemplateContextBuilder - Fluent API
# ============================================================================
def test_builder_should_return_self_from_fluent_methods():
    # Act
    builder = TemplateContextBuilder()
    result1 = builder.with_defaults({})
    result2 = builder.with_variables({})

    # Assert
    actual = (
        result1 is builder,
        result2 is builder,
    )
    expected = (True, True)
    assert actual == expected


def test_builder_should_support_fluent_api_chain():
    # Arrange
    custom_dt = datetime(2026, 1, 17, 10, 30, 45)

    @dataclass
    class Ctx:
        job_name: str

    # Act
    context = (
        TemplateContextBuilder()
        .with_datetime(custom_dt)
        .with_defaults({"env": "dev"})
        .with_variables({"domain": "sales"})
        .with_context(Ctx(job_name="my_job"))
        .build()
    )

    # Assert
    expected = {
        "ds": "2026-01-17",
        "env": "dev",
        "domain": "sales",
        "job_name": "my_job",
    }
    actual = {k: context.get(k) for k in expected}
    assert actual == expected
