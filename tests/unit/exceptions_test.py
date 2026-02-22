import pytest

from tiozin.exceptions import (
    AccessViolationError,
    AlreadyFinishedError,
    AlreadyRunningError,
    JobAlreadyExistsError,
    JobError,
    JobNotFoundError,
    ManifestError,
    NotInitializedError,
    PluginConflictError,
    PluginError,
    PluginNotFoundError,
    PolicyViolationError,
    ProxyError,
    RequiredArgumentError,
    SchemaError,
    SchemaNotFoundError,
    SchemaViolationError,
    TiozinConflictError,
    TiozinForbiddenError,
    TiozinInputError,
    TiozinInternalError,
    TiozinNotFoundError,
    TiozinNotImplementedError,
    TiozinPreconditionError,
    TiozinTimeoutError,
    TiozinUnavailableError,
    TiozinUsageError,
)


# ============================================================================
# Testing TiozinError
# ============================================================================
def test_tiozin_error_should_have_default_attributes():
    # Act
    error = TiozinUsageError()

    # Assert
    actual = (
        bool(error.message),
        error.http_status,
        error.code,
    )
    expected = (True, 400, "TiozinUsageError")
    assert actual == expected


def test_tiozin_error_should_use_custom_attributes_when_provided():
    # Arrange
    custom_message = "Custom error message"
    custom_code = "CUSTOM_ERROR"

    # Act
    error = TiozinUsageError(message=custom_message, code=custom_code)

    # Assert
    actual = (error.message, error.code)
    expected = (custom_message, custom_code)
    assert actual == expected


def test_tiozin_error_to_dict_should_return_code_and_message():
    # Arrange
    error = TiozinUsageError(message="Test message", code="TEST_CODE")

    # Act
    result = error.to_dict()

    # Assert
    actual = result
    expected = {
        "code": "TEST_CODE",
        "message": "Test message",
        "retryable": False,
    }
    assert actual == expected


def test_tiozin_error_str_should_format_code_and_message():
    # Arrange
    error = TiozinUsageError(message="Test message", code="TEST_CODE")

    # Act
    result = str(error)

    # Assert
    actual = result
    expected = "TEST_CODE: Test message"
    assert actual == expected


def test_tiozin_error_raise_if_should_raise_when_condition_is_true():
    # Arrange
    condition = True
    message = "Expected to raise the error"

    # # Act & Assert
    with pytest.raises(TiozinUsageError, match=message):
        TiozinUsageError.raise_if(condition, message)


def test_tiozin_unexpected_error_should_have_default_attributes():
    # Act
    error = TiozinInternalError()

    # Assert
    actual = (
        bool(error.message),
        error.http_status,
        error.code,
    )
    expected = (True, 500, "TiozinInternalError")
    assert actual == expected


# ============================================================================
# Testing Categorical Exceptions
# ============================================================================
def test_categorical_errors_should_have_correct_http_status():
    # Assert
    assert TiozinNotFoundError().http_status == 404
    assert TiozinConflictError().http_status == 409
    assert TiozinInputError().http_status == 422
    assert TiozinTimeoutError().http_status == 408
    assert TiozinForbiddenError().http_status == 403
    assert TiozinPreconditionError().http_status == 412
    assert TiozinUnavailableError().http_status == 503
    assert TiozinNotImplementedError().http_status == 501


@pytest.mark.parametrize(
    "error",
    [
        TiozinTimeoutError(),
        TiozinUnavailableError(),
        AlreadyRunningError(),
    ],
)
def test_retryable_errors_should_have_retryable_true(error):
    assert error.retryable is True


@pytest.mark.parametrize(
    "error",
    [
        TiozinNotFoundError(),
        TiozinConflictError(),
        TiozinInputError(),
        TiozinForbiddenError(),
        TiozinPreconditionError(),
        TiozinNotImplementedError(),
        AlreadyFinishedError(),
    ],
)
def test_non_retryable_errors_should_have_retryable_false(error):
    assert error.retryable is False


# ============================================================================
# Testing JobError
# ============================================================================
def test_job_not_found_error_should_format_job_name_in_message():
    # Arrange
    job_name = "my_job"

    # Act
    error = JobNotFoundError(name=job_name)

    # Assert
    actual = error.message
    expected = "Job `my_job` not found."
    assert actual == expected


def test_job_already_exists_error_should_format_job_name_in_message():
    # Arrange
    job_name = "my_job"

    # Act
    error = JobAlreadyExistsError(name=job_name)

    # Assert
    actual = error.message
    expected = "The job `my_job` already exists."
    assert actual == expected


def test_job_manifest_error_should_format_job_name_when_provided():
    # Arrange
    message = "something is wrong"
    job = "my_job"

    # Act
    error = ManifestError(job, message)

    # Assert
    actual = error.message
    expected = "Invalid manifest `my_job`: something is wrong"
    assert actual == expected


def test_job_manifest_error_from_pydantic_should_format_validation_errors():
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
    assert error.message.startswith("Invalid manifest `test_job`:")


def test_job_manifest_error_from_ruamel_should_format_yaml_errors():
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
    assert error.message.startswith("Invalid manifest `test_job`:")


# ============================================================================
# Testing SchemaError
# ============================================================================
def test_schema_violation_error_should_have_default_message():
    # Act
    error = SchemaViolationError()

    # Assert
    actual = bool(error.message)
    expected = True
    assert actual == expected


def test_schema_not_found_error_should_format_subject_in_message():
    # Arrange
    subject = "user_schema"

    # Act
    error = SchemaNotFoundError(subject=subject)

    # Assert
    actual = error.message
    expected = "Schema `user_schema` not found in the registry."
    assert actual == expected


# ============================================================================
# Testing PluginError
# ============================================================================
def test_plugin_not_found_error_should_format_plugin_name_in_message():
    # Act
    error = PluginNotFoundError(name="my_plugin")

    # Assert
    assert error.message == "Tiozin `my_plugin` not found. Ensure its family is installed."


def test_ambiguous_plugin_error_should_format_plugin_name_and_candidates_in_message():
    # Arrange
    plugin_name = "my_plugin"
    candidates = ["provider1.my_plugin", "provider2.my_plugin"]

    # Act
    error = PluginConflictError(name=plugin_name, candidates=candidates)

    # Assert
    actual = error.message
    expected = (
        "The Tiozin name 'my_plugin' matches multiple registered Tiozin plugins. "
        "Available provider-qualified options are: provider1.my_plugin and provider2.my_plugin. "
        "You can disambiguate by specifying the provider-qualified name "
        "or the fully qualified Python class path."
    )
    assert actual == expected


def test_ambiguous_plugin_error_should_handle_empty_candidates_list():
    # Arrange
    plugin_name = "my_plugin"

    # Act
    error = PluginConflictError(name=plugin_name, candidates=[])

    # Assert
    actual = "" in error.message
    expected = True
    assert actual == expected


def test_plugin_access_violation_error_should_format_plugin_in_message():
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


# ============================================================================
# Testing AlreadyRunningError and AlreadyFinishedError
# ============================================================================
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


# ============================================================================
# Testing PolicyViolationError
# ============================================================================
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


# ============================================================================
# Testing RequiredArgumentError
# ============================================================================
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


# ============================================================================
# Exception Hierarchy Tests
# ============================================================================
@pytest.mark.parametrize(
    "error",
    [
        TiozinNotFoundError(),
        TiozinConflictError(),
        TiozinInputError(),
        TiozinTimeoutError(),
        TiozinForbiddenError(),
        TiozinPreconditionError(),
        TiozinUnavailableError(),
        TiozinNotImplementedError(),
        JobError(),
        JobNotFoundError(name="x"),
        JobAlreadyExistsError(name="x"),
        ManifestError(message="x", manifest="y"),
        SchemaError(),
        SchemaViolationError(),
        SchemaNotFoundError(subject="x"),
        PluginError(),
        PluginNotFoundError(name="x"),
        PluginConflictError(name="x"),
        AlreadyRunningError(),
        AlreadyFinishedError(),
        PolicyViolationError(policy=object),
    ],
)
def test_all_expected_errors_should_be_tiozin_errors(error):
    with pytest.raises(TiozinUsageError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        JobNotFoundError(name="x"),
        JobAlreadyExistsError(name="x"),
    ],
)
def test_job_errors_should_be_catchable_as_job_error(error):
    with pytest.raises(JobError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        SchemaNotFoundError(subject="x"),
        SchemaViolationError(),
    ],
)
def test_schema_errors_should_be_catchable_as_schema_error(error):
    with pytest.raises(SchemaError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        JobNotFoundError(name="test"),
        PluginNotFoundError(name="test"),
    ],
)
def test_errors_should_be_catchable_as_not_found(error):
    with pytest.raises(TiozinNotFoundError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        JobAlreadyExistsError(name="x"),
        PluginConflictError(name="x"),
        AlreadyRunningError(),
        AlreadyFinishedError(),
    ],
)
def test_errors_should_be_catchable_as_conflict(error):
    with pytest.raises(TiozinConflictError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        ManifestError(message="x", manifest="y"),
        SchemaViolationError(),
        PolicyViolationError(policy=object),
    ],
)
def test_errors_should_be_catchable_as_invalid_input(error):
    with pytest.raises(TiozinInputError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        PluginNotFoundError(name="x"),
        PluginConflictError(name="x"),
    ],
)
def test_plugin_errors_should_be_catchable_as_plugin_error(error):
    with pytest.raises(PluginError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        AccessViolationError(name=object()),
        ProxyError("misused decorator"),
        NotInitializedError(),
    ],
)
def test_internal_errors_should_be_catchable_as_internal_error(error):
    with pytest.raises(TiozinInternalError):
        raise error


# ============================================================================
# Testing NotInitializedError
# ============================================================================
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
