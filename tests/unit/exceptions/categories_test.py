import pytest

from tiozin.exceptions import (
    AlreadyFinishedError,
    AlreadyRunningError,
    TiozinConflictError,
    TiozinForbiddenError,
    TiozinInputError,
    TiozinNotFoundError,
    TiozinNotImplementedError,
    TiozinPreconditionError,
    TiozinTimeoutError,
    TiozinUnavailableError,
)


def test_categorical_errors_should_have_http_status():
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
