import pytest

from tiozin.exceptions import (
    AccessViolationError,
    AlreadyFinishedError,
    AlreadyRunningError,
    ManifestError,
    NotInitializedError,
    PolicyViolationError,
    ProxyError,
    RequiredArgumentError,
    TiozinInternalError,
)


def test_manifest_error_should_format_manifest_name_when_provided():
    # Arrange
    message = "something is wrong"
    job = "my_job"

    # Act
    error = ManifestError(job, message)

    # Assert
    actual = error.message
    expected = "Invalid `my_job`: something is wrong"
    assert actual == expected


def test_manifest_error_from_pydantic_should_format_validation_errors():
    # Arrange
    from pydantic import BaseModel, ValidationError

    class TestModel(BaseModel):
        name: int

    with pytest.raises(ValidationError) as exc:
        TestModel(name="not-an-int")

    # Act
    error = ManifestError.from_pydantic("test_job", exc.value)

    # Assert
    assert isinstance(error, ManifestError)
    assert error.message.startswith("Invalid `test_job`:")


def test_manifest_error_from_ruamel_should_format_yaml_errors():
    # Arrange
    from ruamel.yaml import YAML
    from ruamel.yaml.error import MarkedYAMLError

    yaml = YAML()
    yaml_content = """
    key: value
    invalid yaml here: [
    """

    # Act
    with pytest.raises(MarkedYAMLError) as exc:
        yaml.load(yaml_content)

    error = ManifestError.from_ruamel("test_job", exc.value)

    # Assert
    assert isinstance(error, ManifestError)
    assert error.message.startswith("Invalid `test_job`:")


def test_already_running_error_should_format_resource_name_in_message():
    # Arrange
    name = "pipeline"

    # Act
    error = AlreadyRunningError(name=name)

    # Assert
    actual = error.message
    expected = "The pipeline is already running."
    assert actual == expected


def test_already_running_error_should_use_default_resource_name():
    # Act
    error = AlreadyRunningError()

    # Assert
    actual = error.message
    expected = "The resource is already running."
    assert actual == expected


def test_already_finished_error_should_format_resource_name_in_message():
    # Arrange
    name = "pipeline"

    # Act
    error = AlreadyFinishedError(name=name)

    # Assert
    actual = error.message
    expected = "The pipeline has already finished."
    assert actual == expected


def test_already_finished_error_should_use_default_resource_name():
    # Act
    error = AlreadyFinishedError()

    # Assert
    actual = error.message
    expected = "The resource has already finished."
    assert actual == expected


def test_policy_violation_error_should_format_policy_name_and_message():
    # Arrange
    class TestPolicy:
        pass

    custom_message = "Field validation failed"

    # Act
    error = PolicyViolationError(policy=TestPolicy, message=custom_message)

    # Assert
    actual = error.message
    expected = "TestPolicy: Field validation failed."
    assert actual == expected


def test_policy_violation_error_should_use_default_message_when_none_provided():
    # Arrange
    class TestPolicy:
        pass

    # Act
    error = PolicyViolationError(policy=TestPolicy)

    # Assert
    actual = error.message
    expected = "TestPolicy: Execution was denied."
    assert actual == expected


def test_raise_if_missing_should_pass_when_fields_are_set():
    RequiredArgumentError.raise_if_missing(
        name="test",
        org="acme",
        domain="sales",
    )


def test_raise_if_missing_should_pass_when_disabled():
    RequiredArgumentError.raise_if_missing(
        disable_=True,
        name=None,
        org="",
        domain=None,
    )


def test_raise_if_missing_should_pass_when_field_is_excluded():
    RequiredArgumentError.raise_if_missing(
        exclude_=["name"],
        name=None,
        org="acme",
    )


@pytest.mark.parametrize(
    "empty_value",
    [None, "", [], {}, tuple(), set()],
)
def test_raise_if_missing_should_raise_when_field_is_null_or_empty(empty_value):
    with pytest.raises(RequiredArgumentError, match="Missing required fields: 'name'"):
        RequiredArgumentError.raise_if_missing(name=empty_value, org="acme")


def test_raise_if_missing_should_raise_error_when_field_is_not_excluded():
    with pytest.raises(RequiredArgumentError, match="Missing required fields: 'org'"):
        RequiredArgumentError.raise_if_missing(
            exclude_=["name"],
            name=None,
            org=None,
        )


def test_access_violation_error_should_format_plugin_in_message():
    # Arrange
    class FakePlugin:
        def __repr__(self):
            return "FakePlugin(name='test')"

    plugin = FakePlugin()

    # Act
    error = AccessViolationError(name=plugin)

    # Assert
    actual = error.message
    expected = "FakePlugin(name='test') invoked a method reserved for the Tiozin runtime."
    assert actual == expected


def test_not_initialized_error_should_use_default_message_when_none_provided():
    # Act
    error = NotInitializedError()

    # Assert
    assert bool(error.message) is True


def test_not_initialized_error_should_use_custom_message_when_provided():
    # Arrange
    custom_message = "Spark session not initialized for FakeRunner"

    # Act
    error = NotInitializedError(custom_message)

    # Assert
    assert error.message == custom_message


def test_not_initialized_error_should_be_catchable_as_internal_error():
    with pytest.raises(TiozinInternalError):
        raise NotInitializedError()


def test_not_initialized_error_raise_if_should_raise_with_message():
    # Act & Assert
    with pytest.raises(NotInitializedError, match="FakeRunner"):
        NotInitializedError.raise_if(
            True,
            "Spark session not initialized for FakeRunner",
        )


def test_proxy_error_should_be_catchable_as_internal_error():
    with pytest.raises(TiozinInternalError):
        raise ProxyError("misused decorator")
