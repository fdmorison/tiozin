import pytest

from tiozin.exceptions import JobAlreadyExistsError, JobError, JobNotFoundError


def test_job_not_found_error_should_format_job_name_in_message():
    # Arrange
    job_name = "my_job"

    # Act
    error = JobNotFoundError(name=job_name)

    # Assert
    actual = error.message
    expected = "Could not find a job matching `my_job`."
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
