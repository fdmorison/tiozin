import pytest
from duckdb import DuckDBPyRelation

from tiozin.exceptions import RequiredArgumentError, TiozinInputError
from tiozin.family.tio_duckdb import DuckdbPostgresOutput


# =============================================================================
# Testing DuckdbPostgresOutput - Initialization
# =============================================================================
def test_init_should_use_defaults_when_no_params_are_given():
    """
    Simulates initialization with only required arguments.
    The expected result is default values being applied to optional parameters.
    """
    # Act
    output = DuckdbPostgresOutput(name="test", table="events")

    # Assert
    actual = (
        output.mode,
        output.schema,
        output.primary_key,
        output.merge_key,
        output.pre_pgsql,
        output.post_pgsql,
    )
    expected = (
        "APPEND",
        "public",
        [],
        [],
        [],
        [],
    )
    assert actual == expected


def test_init_should_uppercase_mode():
    """
    Simulates initialization with a lowercase mode value.
    The expected result is the mode being normalized to uppercase.
    """
    # Act
    output = DuckdbPostgresOutput(name="test", table="events", mode="truncate")

    # Assert
    actual = output.mode
    expected = "TRUNCATE"
    assert actual == expected


def test_init_should_raise_when_table_is_missing():
    """
    Simulates initialization without providing the required table parameter.
    The expected result is a RequiredArgumentError being raised.
    """
    with pytest.raises(RequiredArgumentError, match="table"):
        DuckdbPostgresOutput(name="test")


@pytest.mark.parametrize("invalid_mode", ["delete", "replace", "insert", "upsert"])
def test_init_should_raise_when_mode_is_invalid(invalid_mode: str):
    """
    Simulates initialization with an unsupported mode.
    The expected result is a TiozinInputError being raised.
    """
    with pytest.raises(TiozinInputError):
        DuckdbPostgresOutput(name="test", table="events", mode=invalid_mode)


# =============================================================================
# Testing DuckdbPostgresOutput - Append Mode
# =============================================================================
def test_write_should_insert_rows_when_appending(customers: DuckDBPyRelation):
    """
    Simulates a first write into a table that does not exist yet using append mode.
    The expected result is the table being created with all incoming rows.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it", table="my_table", mode="append")
    duckdb = output1.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country FROM {output1._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany"),
        (2, "Max Planck", "max@quantum.de", "Germany"),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany"),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany"),
    ]
    assert actual == expected


def test_write_should_duplicate_rows_when_appending_twice(customers: DuckDBPyRelation):
    """
    Simulates a scenario where the same batch is written twice in append mode.
    The expected result is the table containing duplicated rows.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it 1", table="my_table", mode="append")
    output2 = DuckdbPostgresOutput(name="save it 2", table="my_table", mode="append")
    duckdb = output1.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(f"SELECT count(1) FROM {output1._table}").fetchone()[0]
    expected = 2 * customers.count("*").fetchone()[0]
    assert actual == expected


def test_write_should_evolve_schema_when_appending(
    customers: DuckDBPyRelation, customers_evolved: DuckDBPyRelation
):
    """
    Simulates a scenario where an initial batch without the age column is written,
    followed by a second batch including age.

    The expected result is the table containing the new column, with older rows
    having NULL age and newer rows populated.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it 1", table="my_table", mode="append")
    output2 = DuckdbPostgresOutput(name="save it 2", table="my_table", mode="append")
    duckdb = output1.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_evolved)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country,age FROM {output1._table} WHERE age IS NOT NULL ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany", 76),
        (2, "Max Planck", "max@quantum.de", "Germany", 83),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany", 74),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany", 77),
    ]
    assert actual == expected


# =============================================================================
# Testing DuckdbPostgresOutput - Truncate Mode
# =============================================================================
def test_write_should_insert_rows_when_truncating(customers: DuckDBPyRelation):
    """
    Simulates a first write into a table that does not exist yet using truncate mode.
    The expected result is the table being created with all incoming rows.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it", table="my_table", mode="truncate")
    duckdb = output1.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country FROM {output1._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany"),
        (2, "Max Planck", "max@quantum.de", "Germany"),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany"),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany"),
    ]
    assert actual == expected


def test_write_should_update_rows_when_truncating(
    customers: DuckDBPyRelation, customers_updated: DuckDBPyRelation
):
    """
    Simulates a scenario where data is written and later replaced by a corrected batch
    using truncate mode.

    The expected result is the table containing only the most recent version of the data.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it 1", table="my_table", mode="truncate")
    output2 = DuckdbPostgresOutput(name="save it 2", table="my_table", mode="truncate")
    duckdb = output2.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_updated)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country FROM {output2._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany"),
        (2, "Max Planck", "max@quantum.de", "Germany"),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "France"),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany"),
    ]
    assert actual == expected


def test_write_should_evolve_schema_when_truncating(
    customers: DuckDBPyRelation, customers_evolved: DuckDBPyRelation
):
    """
    Simulates a scenario where customers are first written without age and later
    replaced by a batch including age using truncate mode.

    The expected result is the table reflecting only the latest batch with the
    age column populated for all rows.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it 1", table="my_table", mode="truncate")
    output2 = DuckdbPostgresOutput(name="save it 2", table="my_table", mode="truncate")
    duckdb = output2.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_evolved)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country,age FROM {output2._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany", 76),
        (2, "Max Planck", "max@quantum.de", "Germany", 83),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany", 74),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany", 77),
    ]
    assert actual == expected


# =============================================================================
# Testing DuckdbPostgresOutput - Overwrite Mode
# =============================================================================
def test_write_should_insert_rows_when_overwriting(customers: DuckDBPyRelation):
    """
    Simulates a first write into a table that does not exist yet using overwrite mode.
    The expected result is the table being created with all incoming rows.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it", table="my_table", mode="overwrite")
    duckdb = output1.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country FROM {output1._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany"),
        (2, "Max Planck", "max@quantum.de", "Germany"),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany"),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany"),
    ]
    assert actual == expected


def test_write_should_update_rows_when_overwriting(
    customers: DuckDBPyRelation, customers_updated: DuckDBPyRelation
):
    """
    Simulates a scenario where data is written and later replaced by a corrected batch
    using overwrite mode.

    The expected result is the table reflecting only the latest batch.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it 1", table="my_table", mode="overwrite")
    output2 = DuckdbPostgresOutput(name="save it 2", table="my_table", mode="overwrite")
    duckdb = output2.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_updated)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country FROM {output2._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany"),
        (2, "Max Planck", "max@quantum.de", "Germany"),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "France"),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany"),
    ]
    assert actual == expected


def test_write_should_evolve_schema_when_overwriting(
    customers: DuckDBPyRelation, customers_evolved: DuckDBPyRelation
):
    """
    Simulates a scenario where customers are first written without age and later
    replaced by a batch including age using overwrite mode.

    The expected result is the table reflecting the new schema with age populated
    for all rows.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it 1", table="my_table", mode="overwrite")
    output2 = DuckdbPostgresOutput(name="save it 2", table="my_table", mode="overwrite")
    duckdb = output2.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_evolved)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country,age FROM {output2._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany", 76),
        (2, "Max Planck", "max@quantum.de", "Germany", 83),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany", 74),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany", 77),
    ]
    assert actual == expected


# =============================================================================
# Testing DuckdbPostgresOutput - Merge Mode
# =============================================================================
def test_write_should_insert_rows_when_merging(customers: DuckDBPyRelation):
    """
    Simulates a scenario where customers are merged into an empty table.

    The expected result is all incoming rows being inserted.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(name="save it", table="my_table", mode="merge", primary_key="id")
    duckdb = output1.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country FROM {output1._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany"),
        (2, "Max Planck", "max@quantum.de", "Germany"),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany"),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany"),
    ]
    assert actual == expected


def test_write_should_upsert_rows_when_merging(
    customers: DuckDBPyRelation, customers_updated: DuckDBPyRelation
):
    """
    Simulates a scenario where an initial batch is written and a second batch arrives
    with updates for existing keys using merge mode.

    The expected result is matching rows being updated while others remain unchanged.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(
        name="save it 1", table="my_table", mode="merge", primary_key="id"
    )
    output2 = DuckdbPostgresOutput(
        name="save it 2", table="my_table", mode="merge", primary_key="id"
    )
    duckdb = output2.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_updated)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(f"SELECT id,name,country FROM {output2._table} ORDER BY id").fetchall()
    expected = [
        (1, "Albert Einstein", "Germany"),
        (2, "Max Planck", "Germany"),
        (3, "Werner Heisenberg", "France"),
        (4, "Hannah Arendt", "Germany"),
    ]
    assert actual == expected


def test_write_should_evolve_schema_when_merging(
    customers: DuckDBPyRelation, customers_evolved: DuckDBPyRelation
):
    """
    Simulates a scenario where customers are first written without age and later
    merged with a batch including age.

    The expected result is the table including the new column with all rows populated.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(
        name="save it 1", table="my_table", mode="merge", primary_key="id"
    )
    output2 = DuckdbPostgresOutput(
        name="save it 2", table="my_table", mode="merge", primary_key="id"
    )
    duckdb = output2.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_evolved)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(
        f"SELECT id,name,email,country,age FROM {output2._table} ORDER BY id"
    ).fetchall()
    expected = [
        (1, "Albert Einstein", "albert@physics.com", "Germany", 76),
        (2, "Max Planck", "max@quantum.de", "Germany", 83),
        (3, "Werner Heisenberg", "werner@uncertainty.de", "Germany", 74),
        (4, "Hannah Arendt", "hannah@philosophy.de", "Germany", 77),
    ]
    assert actual == expected


def test_write_should_upsert_rows_when_merging_with_explicit_merge_key(
    customers: DuckDBPyRelation, customers_updated: DuckDBPyRelation
):
    """
    Simulates a scenario where merge_key is set to a column different from primary_key.
    Customers are loaded first, then a corrected batch arrives with Werner's country changed
    to France. The conflict key is email instead of id.

    The expected result is Werner's country being updated to France, matched by email.
    """
    # Arrange
    output1 = DuckdbPostgresOutput(
        name="save it 1", table="my_table", mode="merge", primary_key="id", merge_key="email"
    )
    output2 = DuckdbPostgresOutput(
        name="save it 2", table="my_table", mode="merge", primary_key="id", merge_key="email"
    )
    duckdb = output2.duckdb

    # Act
    plan = output1.write(customers)
    duckdb.execute(plan)

    plan = output2.write(customers_updated)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(f"SELECT id,name,country FROM {output2._table} ORDER BY id").fetchall()
    expected = [
        (1, "Albert Einstein", "Germany"),
        (2, "Max Planck", "Germany"),
        (3, "Werner Heisenberg", "France"),
        (4, "Hannah Arendt", "Germany"),
    ]
    assert actual == expected


def test_write_should_raise_when_merging_without_keys(customers: DuckDBPyRelation):
    """
    Simulates a scenario where merge mode is used without providing primary_key or merge_key.

    The expected result is a RequiredArgumentError being raised before any data is written.
    """
    output = DuckdbPostgresOutput(name="save it", table="my_table", mode="merge")
    with pytest.raises(RequiredArgumentError):
        output.write(customers)


# =============================================================================
# Testing DuckdbPostgresOutput - pre_pgsql / post_pgsql Hooks
# =============================================================================
def test_write_should_execute_pre_pgsql_before_write(customers: DuckDBPyRelation):
    """
    Simulates a scenario where pre_pgsql commands are configured before the write.

    The expected result is the pre-execution SQL being applied successfully.
    """
    # Arrange
    output = DuckdbPostgresOutput(
        name="save it",
        table="my_table",
        mode="append",
        pre_pgsql=["CREATE TABLE public.pre_signal (x INT)"],
    )
    duckdb = output.duckdb
    pg_table = f"{output._database}.public.pre_signal"

    # Act
    plan = output.write(customers)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(f"SELECT count(1) FROM {pg_table}").fetchone()[0]
    expected = 0
    assert actual == expected


def test_write_should_execute_post_pgsql_after_write(customers: DuckDBPyRelation):
    """
    Simulates a scenario where post_pgsql commands are configured after the write.

    The expected result is the post-execution SQL being applied successfully.
    """
    # Arrange
    output = DuckdbPostgresOutput(
        name="save it",
        table="my_table",
        mode="append",
        post_pgsql=["CREATE TABLE public.post_signal (x INT)"],
    )
    duckdb = output.duckdb
    pg_table = f"{output._database}.public.post_signal"

    # Act
    plan = output.write(customers)
    duckdb.execute(plan)

    # Assert
    actual = duckdb.sql(f"SELECT count(1) FROM {pg_table}").fetchone()[0]
    expected = 0
    assert actual == expected
