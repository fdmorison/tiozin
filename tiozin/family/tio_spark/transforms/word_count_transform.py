from pyspark.sql import DataFrame
from pyspark.sql.functions import explode, lower, split

from tiozin import Context
from tiozin.utils import as_list, trim

from .. import SparkTransform

DEFAULT_SOURCE_COLUMN = "value"
TOKEN_DELIMITER_RULE = r"[^0-9\p{L}']+"  # use \p{L} for Unicode characters

WORD_FIELD = "word"
COUNT_FIELD = "count"


class SparkWordCountTransform(SparkTransform):
    """
    Counts word occurrences in a Spark DataFrame column.

    This transform tokenizes text rows into words, optionally normalizes them
    to lowercase, and aggregates word counts. Counts can be scoped by one or
    more columns (e.g. document, poem, category).

    By default, the input content is expected in the ``value`` column. The output
    always contains the columns ``word`` and ``count`` with the following schema
    (Spark DDL):

        word STRING, count BIGINT

    When ``count_by`` is used, the grouping columns are included in the output
    schema before ``word`` and ``count``, example:

        document_id INTEGER, word STRING, count BIGINT

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
        SparkWordCountTransform(
            content_field="value",
            lowercase=True,
            count_by="document_id",
        )
        ```

        ```yaml
        transforms:
          - kind: SparkWordCountTransform
            name: word_count
            content_field: value
            lowercase: true
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
        self.content_field = trim(content_field or DEFAULT_SOURCE_COLUMN)
        self.lowercase = lowercase
        self.count_by = as_list(count_by, [])

    def transform(self, context: Context, data: DataFrame) -> DataFrame:
        tokenize = split(
            lower(self.content_field) if self.lowercase else self.content_field,
            TOKEN_DELIMITER_RULE,
        )

        tokens = data.select(
            *self.count_by,
            explode(tokenize).alias(WORD_FIELD),
        )

        grouping_cols = [*self.count_by, WORD_FIELD]

        return (
            tokens.groupBy(grouping_cols).count().filter(f"{WORD_FIELD} != ''").sort(grouping_cols)
        )
