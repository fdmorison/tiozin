from duckdb import DuckDBPyRelation

from tiozin.api import Context, conventions
from tiozin.utils import as_list

from .. import DuckdbTransform

TOKEN_DELIMITER_RULE = r"[^0-9\p{L}'']+"

WORD_FIELD = "word"
COUNT_FIELD = "count"


class DuckdbWordCountTransform(DuckdbTransform):
    """
    Counts word occurrences in a DuckDB relation.

    This transform tokenizes text rows into words using a regular expression,
    optionally normalizes them to lowercase, and aggregates word counts.
    All processing is performed in SQL using DuckDB built-in functions.

    The input relation is referenced by its registered alias, which is
    automatically assigned by the DuckDB step proxy. The transform splits
    the configured content column into tokens, expands them into rows, and
    computes word frequencies.

    Word counts can optionally be scoped by one or more columns using
    ``count_by``. When provided, these columns are included in the grouping
    key, allowing counts per document, category, or any other dimension.

    The output schema always includes the columns ``word`` and ``count``.
    When ``count_by`` is used, grouping columns appear before them.

    This transform mirrors the behavior and semantics of common word count
    implementations in engines such as Spark, while leveraging DuckDB’s
    SQL-first execution model.

    Attributes:
        content_field:
            Name of the column containing the textual content to be tokenized.
            Defaults to ``value``.

        count_by:
            Column name or list of column names used to scope the word counts.
            Optional.

        lowercase:
            Whether to normalize words to lowercase before counting.
            Defaults to ``True``.

    Examples:

        ```python
        DuckdbWordCountTransform(
            content_field="value",
            lowercase=True,
            count_by="document_id",
        )
        ```

        ```yaml
        transforms:
          - kind: DuckdbWordCountTransform
            name: word_count
            content_field: value
            lowercase: true
            count_by: document_id
        ```
    """

    def __init__(
        self,
        content_field: str = None,
        count_by: str | list[str] = None,
        lowercase: bool = True,
        **options,
    ) -> None:
        super().__init__(**options)
        self.content_field = content_field or conventions.CONTENT_COLUMN
        self.lowercase = lowercase
        self.count_by = as_list(count_by, [])

    def transform(self, _: Context, data: DuckDBPyRelation) -> DuckDBPyRelation:
        text = f"lower({self.content_field})" if self.lowercase else self.content_field

        group = ", ".join(self.count_by) + "," if self.count_by else ""
        group_with_word = ", ".join([*self.count_by, WORD_FIELD])

        sql = f"""
        SELECT
            {group_with_word},
            count(1) AS {COUNT_FIELD}
        FROM (
            SELECT
                {group}
                unnest(regexp_split_to_array({text},'{TOKEN_DELIMITER_RULE}')) AS {WORD_FIELD}
            FROM {data.alias}
        )
        WHERE {WORD_FIELD} != ''
        GROUP BY {group_with_word}
        ORDER BY {group_with_word}
        """
        return self.duckdb.sql(sql)
