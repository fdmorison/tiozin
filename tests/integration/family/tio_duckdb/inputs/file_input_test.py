from tiozin.family.tio_duckdb import DuckdbFileInput

BASE_PATH = "./tests/mocks/data"


# =============================================================================
# Testing DuckdbFileInput - Initialization
# =============================================================================
def test_input_should_default_to_parquet_format():
    # Act
    input = DuckdbFileInput(name="test", path="/tmp/data")

    # Assert
    actual = input.format
    expected = "parquet"
    assert actual == expected


def test_input_should_default_to_relation_mode():
    # Act
    input = DuckdbFileInput(name="test", path="/tmp/data")

    # Assert
    actual = input.mode
    expected = "relation"
    assert actual == expected


def test_input_should_default_to_hive_partitioning_enabled():
    # Act
    input = DuckdbFileInput(name="test", path="/tmp/data")

    # Assert
    actual = input.hive_partitioning
    expected = True
    assert actual == expected


def test_input_should_default_to_union_by_name_enabled():
    # Act
    input = DuckdbFileInput(name="test", path="/tmp/data")

    # Assert
    actual = input.union_by_name
    expected = True
    assert actual == expected


def test_input_should_default_to_explode_filepath_disabled():
    # Act
    input = DuckdbFileInput(name="test", path="/tmp/data")

    # Assert
    actual = input.explode_filepath
    expected = False
    assert actual == expected


# =============================================================================
# Testing DuckdbFileInput - Read Delegation
# =============================================================================
def test_input_should_read_files_via_builder():
    """Delegates reading to ReadBuilder and returns a DuckDB relation."""
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
    expected = [("spark", "hello spark"), ("world", "hello world")]
    assert actual == expected


def test_input_should_forward_options_to_builder():
    """Custom **options are forwarded to the builder."""
    # Arrange
    path = f"{BASE_PATH}/csv/sample.csv"
    context = None

    # Act
    relation = DuckdbFileInput(
        name="test",
        path=path,
        format="csv",
        header=True,
        delim=",",
    ).read(context)

    # Assert
    actual = sorted(relation.fetchall())
    expected = [("spark", "hello spark"), ("world", "hello world")]
    assert actual == expected
