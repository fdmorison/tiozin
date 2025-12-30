import pytest

from tiozin.exceptions import (
    AlreadyFinishedError,
    AlreadyRunningError,
    AmbiguousPluginError,
    ConflictError,
    InvalidInputError,
    JobAlreadyExistsError,
    JobError,
    JobManifestError,
    JobNotFoundError,
    NotFoundError,
    OperationTimeoutError,
    PluginError,
    PluginKindError,
    PluginNotFoundError,
    PolicyViolationError,
    SchemaError,
    SchemaNotFoundError,
    SchemaViolationError,
    TiozinError,
    TiozinUnexpectedError,
)


# ============================================================================
# Testing TiozinError
# ============================================================================
def test_tiozin_error_should_have_default_attributes():
    # Act
    error = TiozinError()

    # Assert
    actual = (
        bool(error.message),
        error.http_status,
        error.code,
    )
    expected = (True, 400, "TiozinError")
    assert actual == expected


def test_tiozin_error_should_use_custom_attributes_when_provided():
    # Arrange
    custom_message = "Custom error message"
    custom_code = "CUSTOM_ERROR"

    # Act
    error = TiozinError(message=custom_message, code=custom_code)

    # Assert
    actual = (error.message, error.code)
    expected = (custom_message, custom_code)
    assert actual == expected


def test_tiozin_error_to_dict_should_return_code_and_message():
    # Arrange
    error = TiozinError(message="Test message", code="TEST_CODE")

    # Act
    result = error.to_dict()

    # Assert
    actual = result
    expected = {
        "code": "TEST_CODE",
        "message": "Test message",
        "http_status": 400,
    }
    assert actual == expected


def test_tiozin_error_str_should_format_code_and_message():
    # Arrange
    error = TiozinError(message="Test message", code="TEST_CODE")

    # Act
    result = str(error)

    # Assert
    actual = result
    expected = "TEST_CODE: Test message"
    assert actual == expected


def test_tiozin_unexpected_error_should_have_default_attributes():
    # Act
    error = TiozinUnexpectedError()

    # Assert
    actual = (
        bool(error.message),
        error.http_status,
        error.code,
    )
    expected = (True, 500, "TiozinUnexpectedError")
    assert actual == expected


# ============================================================================
# Testing Categorical Exceptions
# ============================================================================
def test_categorical_errors_should_have_correct_http_status():
    # Act
    not_found = NotFoundError()
    conflict = ConflictError()
    invalid_input = InvalidInputError()
    timeout = OperationTimeoutError()

    # Assert
    actual = (
        not_found.http_status,
        conflict.http_status,
        invalid_input.http_status,
        timeout.http_status,
    )
    expected = (404, 409, 422, 408)
    assert actual == expected


# ============================================================================
# Testing JobError
# ============================================================================
def test_job_not_found_error_should_format_job_name_in_message():
    # Arrange
    job_name = "my_job"

    # Act
    error = JobNotFoundError(job_name=job_name)

    # Assert
    actual = error.message
    expected = "Job `my_job` not found."
    assert actual == expected


def test_job_already_exists_error_should_format_job_name_in_message():
    # Arrange
    job_name = "my_job"

    # Act
    error = JobAlreadyExistsError(job_name=job_name)

    # Assert
    actual = error.message
    expected = "The job `my_job` already exists."
    assert actual == expected


def test_job_manifest_error_should_format_job_name_when_provided():
    # Arrange
    message = "something is wrong"
    job = "my_job"

    # Act
    error = JobManifestError(message=message, job=job)

    # Assert
    actual = error.message
    expected = "Invalid manifest for `my_job`: something is wrong"
    assert actual == expected


def test_job_manifest_error_from_pydantic_should_format_validation_errors():
    # Arrange
    from pydantic import BaseModel, ValidationError

    class TestModel(BaseModel):
        name: int

    with pytest.raises(ValidationError) as exc:
        TestModel(name="not-an-int")

    # Act
    error = JobManifestError.from_pydantic(exc.value, job="test_job")

    # Assert
    assert isinstance(error, JobManifestError)
    assert error.message.startswith("Invalid manifest for `test_job`:")


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

    error = JobManifestError.from_ruamel(exc.value, job="test_job")

    # Assert
    assert isinstance(error, JobManifestError)
    assert error.message.startswith("Invalid manifest for `test_job`:")


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
    # Arrange
    plugin_name = "my_plugin"

    # Act
    error = PluginNotFoundError(plugin_name=plugin_name)

    # Assert
    actual = error.message
    expected = "Plugin `my_plugin` not found."
    assert actual == expected


def test_ambiguous_plugin_error_should_format_plugin_name_and_candidates_in_message():
    # Arrange
    plugin_name = "my_plugin"
    candidates = ["provider1.my_plugin", "provider2.my_plugin"]

    # Act
    error = AmbiguousPluginError(plugin_name=plugin_name, candidates=candidates)

    # Assert
    actual = error.message
    expected = (
        "The plugin name 'my_plugin' matches multiple registered plugins. "
        "Available provider-qualified options are: provider1.my_plugin, provider2.my_plugin. "
        "You can disambiguate by specifying the provider-qualified name "
        "or the fully qualified Python class path."
    )
    assert actual == expected


def test_ambiguous_plugin_error_should_handle_empty_candidates_list():
    # Arrange
    plugin_name = "my_plugin"

    # Act
    error = AmbiguousPluginError(plugin_name=plugin_name, candidates=[])

    # Assert
    actual = "" in error.message
    expected = True
    assert actual == expected


def test_plugin_kind_error_should_format_plugin_name_and_kind_in_message():
    # Arrange
    plugin_name = "my_plugin"
    plugin_kind = dict

    # Act
    error = PluginKindError(plugin_name=plugin_name, plugin_kind=plugin_kind)

    # Assert
    actual = error.message
    expected = "Plugin 'my_plugin' cannot be used as 'dict'."
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
    expected = "The `pipeline` is already running."
    assert actual == expected


def test_already_running_error_should_use_default_resource_name():
    # Act
    error = AlreadyRunningError()

    # Assert
    actual = error.message
    expected = "The `resource` is already running."
    assert actual == expected


def test_already_finished_error_should_format_resource_name_in_message():
    # Arrange
    name = "pipeline"

    # Act
    error = AlreadyFinishedError(name=name)

    # Assert
    actual = error.message
    expected = "The `pipeline` has already finished."
    assert actual == expected


def test_already_finished_error_should_use_default_resource_name():
    # Act
    error = AlreadyFinishedError()

    # Assert
    actual = error.message
    expected = "The `resource` has already finished."
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
# Exception Hierarchy Tests
# ============================================================================
@pytest.mark.parametrize(
    "error",
    [
        NotFoundError(),
        ConflictError(),
        InvalidInputError(),
        OperationTimeoutError(),
        JobError(),
        JobNotFoundError(job_name="x"),
        JobAlreadyExistsError(job_name="x"),
        JobManifestError(message="x", job="y"),
        SchemaError(),
        SchemaViolationError(),
        SchemaNotFoundError(subject="x"),
        PluginError(),
        PluginNotFoundError(plugin_name="x"),
        PluginKindError(plugin_name="x", plugin_kind=object),
        AmbiguousPluginError(plugin_name="x"),
        AlreadyRunningError(),
        AlreadyFinishedError(),
        PolicyViolationError(policy=object),
    ],
)
def test_all_expected_errors_are_tiozin_errors(error):
    with pytest.raises(TiozinError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        JobNotFoundError(job_name="x"),
        JobAlreadyExistsError(job_name="x"),
        JobManifestError(message="x", job="y"),
    ],
)
def test_job_errors_are_catchable_as_job_error(error):
    with pytest.raises(JobError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        SchemaNotFoundError(subject="x"),
        SchemaViolationError(),
    ],
)
def test_schema_errors_are_catchable_as_schema_error(error):
    with pytest.raises(SchemaError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        JobNotFoundError(job_name="test"),
        PluginNotFoundError(plugin_name="test"),
    ],
)
def test_errors_are_catchable_as_not_found(error):
    with pytest.raises(NotFoundError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        JobAlreadyExistsError(job_name="x"),
        AmbiguousPluginError(plugin_name="x"),
        AlreadyRunningError(),
        AlreadyFinishedError(),
    ],
)
def test_errors_are_catchable_as_conflict(error):
    with pytest.raises(ConflictError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        JobManifestError(message="x", job="y"),
        PluginKindError(plugin_name="x", plugin_kind=object),
        SchemaViolationError(),
        PolicyViolationError(policy=object),
    ],
)
def test_errors_are_catchable_as_invalid_input(error):
    with pytest.raises(InvalidInputError):
        raise error


@pytest.mark.parametrize(
    "error",
    [
        PluginNotFoundError(plugin_name="x"),
        AmbiguousPluginError(plugin_name="x"),
        PluginKindError(plugin_name="x", plugin_kind=object),
    ],
)
def test_plugin_errors_are_catchable_as_plugin_error(error):
    with pytest.raises(PluginError):
        raise error
