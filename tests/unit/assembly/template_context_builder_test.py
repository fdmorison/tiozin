from dataclasses import dataclass, field
from datetime import datetime

import pytest
from assertpy import assert_that

from tiozin.assembly.template_context_builder import TemplateContextBuilder
from tiozin.exceptions import TiozinUnexpectedError
from tiozin.utils.relative_date import RelativeDate

# ============================================================================
# Testing Basic Build
# ============================================================================


def test_build_should_return_immutable_context():
    # Arrange
    builder = TemplateContextBuilder()

    # Act
    context = builder.build()

    # Assert
    with pytest.raises(TypeError):
        context["new_key"] = "value"


def test_build_should_include_relative_date_when_datetime_is_enabled():
    # Arrange
    builder = TemplateContextBuilder().with_relative_date()

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    assert_that(actual).contains_key("DAY")
    assert_that(actual["DAY"]).is_instance_of(RelativeDate)


def test_build_should_expose_relative_date_properties():
    # Arrange
    builder = TemplateContextBuilder().with_relative_date()

    # Act
    context = builder.build()

    # Assert
    actual = set(context.keys())
    expected = {"ds", "ts", "iso", "YYYY", "MM", "DD"}
    assert_that(expected).is_subset_of(actual)


# ============================================================================
# Testing with_relative_date
# ============================================================================


def test_build_should_use_relative_date_when_provided():
    # Arrange
    custom_datetime = datetime(2025, 6, 15, 12, 30, 45)
    builder = TemplateContextBuilder().with_relative_date(custom_datetime)

    # Act
    context = builder.build()

    # Assert
    actual = {
        "ds": context["ds"],
        "YYYY": context["YYYY"],
        "MM": context["MM"],
        "DD": context["DD"],
        "today": str(context["today"]),
    }
    expected = {
        "ds": "2025-06-15",
        "YYYY": "2025",
        "MM": "06",
        "DD": "15",
        "today": "2025-06-15",
    }
    assert actual == expected


def test_with_relative_date_should_reject_non_datetime_values():
    # Arrange
    builder = TemplateContextBuilder()

    # Act & Assert
    with pytest.raises(TypeError, match="nominal_date must be a datetime"):
        builder.with_relative_date("2025-06-15")


# ============================================================================
# Testing with_defaults
# ============================================================================


def test_build_should_include_default_values():
    # Arrange
    builder = TemplateContextBuilder().with_defaults(
        {
            "foo": "production",
            "bar": "us-east",
        }
    )

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    expected = {
        "foo": "production",
        "bar": "us-east",
    }
    assert_that(expected).is_subset_of(actual)


def test_build_should_override_default_value_when_new_value_is_provided():
    # Arrange
    builder = (
        TemplateContextBuilder()
        .with_defaults({"foo": "old_value"})
        .with_variables({"foo": "new_value"})
    )

    # Act
    context = builder.build()

    # Assert
    actual = context.get("foo")
    expected = "new_value"
    assert_that(actual).is_equal_to(expected)


def test_with_defaults_should_reject_non_mapping_values():
    # Arrange
    builder = TemplateContextBuilder()

    # Act & Assert
    with pytest.raises(TypeError, match="defaults must be a mapping"):
        builder.with_defaults("not a mapping")


def test_build_should_merge_multiple_default_assignments():
    # Arrange
    builder = (
        TemplateContextBuilder()
        .with_defaults({"first_default": "value_from_first_call"})
        .with_defaults({"second_default": "value_from_second_call"})
    )

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    expected = {
        "first_default": "value_from_first_call",
        "second_default": "value_from_second_call",
    }
    assert_that(expected).is_subset_of(actual)


# ============================================================================
# Testing with_variables
# ============================================================================


def test_build_should_include_variables():
    # Arrange
    builder = TemplateContextBuilder().with_variables(
        {
            "business_domain": "sales",
            "entity_name": "orders",
        }
    )

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    expected = {
        "business_domain": "sales",
        "entity_name": "orders",
    }
    assert_that(expected).is_subset_of(actual)


def test_with_variables_should_reject_non_mapping_values():
    # Arrange
    builder = TemplateContextBuilder()

    # Act & Assert
    with pytest.raises(TypeError, match="vars must be a mapping"):
        builder.with_variables(["not", "a", "mapping"])


def test_build_should_merge_multiple_variable_assignments():
    # Arrange
    builder = (
        TemplateContextBuilder()
        .with_variables({"first_variable": "value_from_first_call"})
        .with_variables({"second_variable": "value_from_second_call"})
    )

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    expected = {
        "first_variable": "value_from_first_call",
        "second_variable": "value_from_second_call",
    }
    assert_that(expected).is_subset_of(actual)


def test_build_should_override_previous_variable_value_for_same_key():
    # Arrange
    builder = (
        TemplateContextBuilder()
        .with_variables({"conflicting_key": "old_value"})
        .with_variables({"conflicting_key": "new_value"})
    )

    # Act
    context = builder.build()

    # Assert
    actual = context.get("conflicting_key")
    expected = "new_value"
    assert_that(actual).is_equal_to(expected)


# ============================================================================
# Testing with_context (dataclass)
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


def test_build_should_include_public_dataclass_fields():
    # Arrange
    ctx = SampleContext(name="test", value=42, secret="hidden")
    builder = TemplateContextBuilder().with_context(ctx)

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    expected = {
        "name": "test",
        "value": 42,
    }
    assert_that(expected).is_subset_of(actual)


def test_build_should_exclude_fields_marked_as_template_false():
    # Arrange
    ctx = SampleContext(name="test", value=42, secret="hidden")
    builder = TemplateContextBuilder().with_context(ctx)

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    assert_that(actual).does_not_contain_key("secret")


def test_build_should_include_fields_without_metadata():
    # Arrange
    ctx = ContextWithoutMetadata(name="test", value=42)
    builder = TemplateContextBuilder().with_context(ctx)

    # Act
    context = builder.build()

    # Assert
    actual = dict(context)
    expected = {
        "name": "test",
        "value": 42,
    }
    assert_that(expected).is_subset_of(actual)


def test_with_context_should_reject_non_dataclass_instances():
    # Arrange
    builder = TemplateContextBuilder()

    # Act & Assert
    with pytest.raises(TypeError, match="context must be a dataclass instance"):
        builder.with_context({"not": "dataclass"})


# ============================================================================
# Testing with_envvars
# ============================================================================
def test_build_should_create_env_namespace_when_with_enabled(monkeypatch):
    # Arrange
    monkeypatch.setenv("OS_VARIABLE", "foo")
    builder = TemplateContextBuilder().with_envvars()

    # Act
    context = builder.build()

    # Assert
    actual = context.get("ENV")
    expected = {
        "OS_VARIABLE": "foo",
    }
    assert_that(expected).is_subset_of(actual)


def test_builder_should_isolate_envvars_in_env_namespace(monkeypatch):
    # Arrange
    monkeypatch.setenv("OS_VARIABLE", "from_os")
    builder = (
        TemplateContextBuilder()
        .with_envvars()
        .with_defaults({"OS_VARIABLE": "from_user"})
        .with_variables({"OS_VARIABLE": "from_user"})
    )

    # Act
    context = builder.build()

    # Assert
    actual = {
        "OS_VARIABLE": context.get("OS_VARIABLE"),
        "ENV": {
            "OS_VARIABLE": context.get("ENV", {}).get("OS_VARIABLE"),
        },
    }
    expected = {
        "OS_VARIABLE": "from_user",
        "ENV": {
            "OS_VARIABLE": "from_os",
        },
    }
    assert_that(expected).is_subset_of(actual)


def test_build_should_merge_existing_env_with_loaded_envvars(monkeypatch):
    # Arrange
    monkeypatch.setenv("OS_VARIABLE", "from_os")

    builder = (
        TemplateContextBuilder()
        .with_variables(
            {"ENV": {"USER_VARIABLE": "from_user"}},
        )
        .with_envvars()
    )

    # Act
    context = builder.build()

    # Assert
    actual = context.get("ENV")
    expected = {
        "OS_VARIABLE": "from_os",
        "USER_VARIABLE": "from_user",
    }
    assert_that(expected).is_subset_of(actual)


def test_build_should_give_precedence_to_os_env_over_user_env(monkeypatch):
    # Arrange
    monkeypatch.setenv("SHARED_KEY", "from_os")

    builder = (
        TemplateContextBuilder()
        .with_variables(
            {"ENV": {"SHARED_KEY": "from_user"}},
        )
        .with_envvars()
    )

    # Act
    context = builder.build()

    # Assert
    actual = context.get("ENV", {}).get("SHARED_KEY")
    expected = "from_os"
    assert actual == expected


def test_build_should_raise_if_env_is_not_a_mapping():
    # Arrange
    builder = (
        TemplateContextBuilder()
        .with_variables(
            {"ENV": "not-a-mapping"},
        )
        .with_envvars()
    )

    # Act & Assert
    with pytest.raises(TiozinUnexpectedError, match="ENV must be a mapping"):
        builder.build()


def test_with_envvars_should_be_idempotent(monkeypatch):
    # Arrange
    monkeypatch.setenv("OS_VARIABLE", "foo")

    builder = TemplateContextBuilder().with_envvars().with_envvars()

    # Act
    context = builder.build()

    # Assert
    actual = context.get("ENV")
    expected = {
        "OS_VARIABLE": "foo",
    }
    assert_that(expected).is_subset_of(actual)


# ============================================================================
# Testing Precedence
# ============================================================================


def test_build_should_give_precedence_to_variables_over_defaults():
    # Arrange
    builder = (
        TemplateContextBuilder()
        .with_defaults({"conflicting_key": "old_value"})
        .with_variables({"conflicting_key": "new_value"})
    )

    # Act
    context = builder.build()

    # Assert
    actual = context["conflicting_key"]
    expected = "new_value"
    assert_that(actual).is_equal_to(expected)


def test_build_should_give_precedence_to_context_over_variables():
    # Arrange
    @dataclass
    class ContextPayload:
        conflicting_key: str

    ctx = ContextPayload(conflicting_key="value_from_context")

    builder = (
        TemplateContextBuilder()
        .with_variables({"conflicting_key": "value_from_variables"})
        .with_context(ctx)
    )

    # Act
    context = builder.build()

    # Assert
    actual = context["conflicting_key"]
    expected = "value_from_context"
    assert_that(actual).is_equal_to(expected)


def test_build_should_give_precedence_to_date_properties_over_all_other_sources():
    # Arrange
    builder = (
        TemplateContextBuilder()
        .with_relative_date()
        .with_defaults({"ds": "default_value"})
        .with_variables({"ds": "variable_value"})
    )

    # Act
    context = builder.build()

    # Assert
    actual = context.get("ds")
    non_expected = {"default_value", "variable_value"}
    assert actual not in non_expected
