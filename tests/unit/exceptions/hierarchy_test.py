import pytest

from tiozin.exceptions import (
    AccessViolationError,
    AlreadyFinishedError,
    AlreadyRunningError,
    JobAlreadyExistsError,
    JobError,
    JobNotFoundError,
    ModelError,
    NotInitializedError,
    PluginConflictError,
    PluginError,
    PluginNotFoundError,
    PolicyViolationError,
    ProxyError,
    SchemaError,
    SchemaNotFoundError,
    SchemaViolationError,
    SettingsError,
    SettingsNotFoundError,
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
        ModelError(message="x", model="y"),
        SchemaError(),
        SchemaViolationError(),
        SchemaNotFoundError(subject="x"),
        SettingsError(),
        SettingsNotFoundError(location="x"),
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
        JobNotFoundError(name="test"),
        PluginNotFoundError(name="test"),
        SettingsNotFoundError(location="test"),
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
        ModelError(message="x", model="y"),
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
        AccessViolationError(name=object()),
        ProxyError("misused decorator"),
        NotInitializedError(),
    ],
)
def test_internal_errors_should_be_catchable_as_internal_error(error):
    with pytest.raises(TiozinInternalError):
        raise error
