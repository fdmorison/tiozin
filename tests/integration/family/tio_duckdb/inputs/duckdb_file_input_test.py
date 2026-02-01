import pytest

from tiozin.family.tio_duckdb import DuckdbFileInput

BASE_PATH = "./tests/mocks/data"


# =============================================================================
# Testing DuckdbFileInput - Core Behavior
# =============================================================================
def test_input_should_read_text_files():
    """Reads plain text files into a DuckDB relation."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    context = None

    # Act
    relation = DuckdbFileInput(
        name="test",
        path=path,
        format="text",
    ).read(context)

    # Assert
    actual = relation.fetchall()
    expected = [("hello world\nhello spark\n",)]
    assert actual == expected


def test_input_should_read_json_files():
    """Reads JSON files into a DuckDB relation."""
    # Arrange
    path = f"{BASE_PATH}/json/sample.json"
    context = None

    # Act
    relation = DuckdbFileInput(
        name="test",
        path=path,
        format="json",
    ).read(context)

    # Assert
    actual = sorted(relation.fetchall())
    expected = [("hello spark",), ("hello world",)]
    assert actual == expected


def test_input_should_read_parquet_files():
    """Reads Parquet files into a DuckDB relation."""
    # Arrange
    path = f"{BASE_PATH}/parquet/sample.parquet"
    context = None

    # Act
    relation = DuckdbFileInput(
        name="test",
        path=path,
        format="parquet",
    ).read(context)

    # Assert
    actual = sorted(relation.fetchall())
    expected = [("hello spark",), ("hello world",)]
    assert actual == expected


def test_input_should_read_csv_files():
    """Reads CSV files into a DuckDB relation."""
    # Arrange
    path = f"{BASE_PATH}/csv/sample.csv"
    context = None

    # Act
    relation = DuckdbFileInput(
        name="test",
        path=path,
        format="csv",
    ).read(context)

    # Assert
    actual = sorted(relation.fetchall())
    expected = [("hello spark",), ("hello world",)]
    assert actual == expected


# =============================================================================
# Testing DuckdbFileInput - File Metadata
# =============================================================================
@pytest.mark.parametrize(
    "format,path,filename,filestem,filetype",
    [
        ("text", f"{BASE_PATH}/text/sample", "sample", "sample", ""),
        ("text", f"{BASE_PATH}/text/sample.txt", "sample.txt", "sample", "txt"),
        ("json", f"{BASE_PATH}/json/sample.json", "sample.json", "sample", "json"),
    ],
)
def test_input_should_include_file_metadata_when_enabled(
    format: str,
    path: str,
    filename: str,
    filestem: str,
    filetype: str,
):
    """Adds file metadata columns (dirpath, dirname, filename, filestem, filetype) when enabled."""
    # Arrange
    context = None

    # Act
    relation = DuckdbFileInput(
        name="test",
        path=path,
        format=format,
        include_file_metadata=True,
    ).read(context)

    # Assert
    rows = relation.fetchall()
    actual = {
        col: rows[0][i]
        for i, col in enumerate(relation.columns)
        if col in ("filename", "filestem", "filetype")
    }
    expected = {"filename": filename, "filestem": filestem, "filetype": filetype}
    assert actual == expected


def test_input_should_not_include_file_metadata_by_default():
    """File metadata columns are absent when include_file_metadata is False (default)."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    context = None

    # Act
    relation = DuckdbFileInput(
        name="test",
        path=path,
        format="text",
    ).read(context)

    # Assert
    actual = relation.columns
    expected = ["value"]
    assert actual == expected


# =============================================================================
# Testing DuckdbFileInput - Unsupported Format
# =============================================================================
def test_input_should_raise_error_for_unsupported_format():
    """Raises InvalidInputError for unsupported file formats."""
    from tiozin.exceptions import InvalidInputError

    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    context = None

    # Act / Assert
    with pytest.raises(InvalidInputError, match="does not support"):
        DuckdbFileInput(
            name="test",
            path=path,
            format="my_format",
        ).read(context)
