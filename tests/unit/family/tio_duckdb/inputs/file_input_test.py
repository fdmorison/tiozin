import pytest

from tiozin.family.tio_duckdb import DuckdbFileInput

# ============================================================================
# Testing DuckdbFileInput.static_datasets — one dataset per path
# ============================================================================


@pytest.mark.parametrize(
    "path, expected",
    [
        (
            "s3://my-bucket/data/file.parquet",
            [("s3://my-bucket", "data/file.parquet")],
        ),
        (
            ["s3://my-bucket/a.parquet", "gs://other-bucket/b.parquet"],
            [
                ("s3://my-bucket", "a.parquet"),
                ("gs://other-bucket", "b.parquet"),
            ],
        ),
    ],
    ids=["single-path", "multi-path"],
)
def test_file_input_should_return_one_dataset_per_path(path, expected):
    # Arrange
    step = DuckdbFileInput(name="test", path=path)

    # Act
    result = step.static_datasets()

    # Assert
    actual = [(d.tiozin_namespace, d.tiozin_name) for d in result.inputs]
    assert actual == expected
