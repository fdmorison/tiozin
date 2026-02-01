import pytest

from tiozin.api import conventions


# =============================================================================
# Testing conventions - Prefixes
# =============================================================================
@pytest.mark.parametrize(
    "constant,expected",
    [
        ("SYSTEM_PREFIX", "_tio_"),
        ("INTERNAL_PREFIX", "__tio_"),
    ],
)
def test_prefix_should_have_expected_value(constant: str, expected: str):
    """Tiozin prefixes follow the naming convention."""
    # Act
    actual = getattr(conventions, constant)

    # Assert
    assert actual == expected


# =============================================================================
# Testing conventions - Column Names
# =============================================================================
@pytest.mark.parametrize(
    "constant,expected",
    [
        ("CONTENT_COLUMN", "value"),
        ("DIRPATH_COLUMN", "dirpath"),
        ("DIRNAME_COLUMN", "dirname"),
        ("FILESIZE_COLUMN", "filesize"),
        ("FILEPATH_COLUMN", "filepath"),
        ("FILENAME_COLUMN", "filename"),
        ("FILESTEM_COLUMN", "filestem"),
        ("FILETYPE_COLUMN", "filetype"),
    ],
)
def test_column_constant_should_have_expected_value(constant: str, expected: str):
    """File metadata column names are stable and lowercase."""
    # Act
    actual = getattr(conventions, constant)

    # Assert
    assert actual == expected


# =============================================================================
# Testing conventions - Column Name Uniqueness
# =============================================================================
def test_file_metadata_columns_should_be_unique():
    """All file metadata column constants must map to distinct names."""
    # Arrange
    columns = [
        conventions.CONTENT_COLUMN,
        conventions.DIRPATH_COLUMN,
        conventions.DIRNAME_COLUMN,
        conventions.FILESIZE_COLUMN,
        conventions.FILEPATH_COLUMN,
        conventions.FILENAME_COLUMN,
        conventions.FILESTEM_COLUMN,
        conventions.FILETYPE_COLUMN,
    ]

    # Act
    actual = len(set(columns))

    # Assert
    expected = len(columns)
    assert actual == expected
