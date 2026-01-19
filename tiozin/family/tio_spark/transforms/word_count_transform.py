from pyspark.sql import DataFrame
from pyspark.sql.functions import col, explode, lower, split

from tiozin import StepContext, Transform
from tiozin.utils.helpers import as_list

DEFAULT_SOURCE_COLUMN = "value"
TOKEN_DELIMITER_RULE = r"[^0-9\p{L}']+"  # use \p{L} for Unicode characters

WORD_FIELD = "word"
COUNT_FIELD = "count"


class SparkWordCountTransform(Transform):
    """
    Performs a word count on text data contained in a Spark DataFrame.

    It splits the text in the specified `text_field` into words, optionally converts them
    to lowercase, and computes the total count for each word.

    Input Schema:
        - "value STRING" or
        - "key STRING, value STRING"

    Output Schema:
        - "word STRING, count BIGINT" or
        - "key STRING, word STRING, count BIGINT"

    Attributes:
        text_field: Name of the column containing the text. Default: 'value'.
        lowercase: Whether to convert words to lowercase before counting. Default: True.
        group_by: Column name or list of column names to aggregate counts by. Optional.

    Examples:

        ```python
        SparkWordCountTransformer(
             text_field="value",
             lowercase=True,
         )
        ```

        ```yaml
        transformers:
            - type: SparkWordCountTransformer
              text_field: value
              lowercase: true
        ```

        Input DataFrame                          Output DataFrame
        +----------------------------------+     +------+-----+
        | value                            |     | word |count|
        +----------------------------------+     +------+-----+
        | lorem ipsum dolor sit amet       |     | amet |   1 |
        | lorem lorem dolor sit sit sit sit| ==> | dolor|   2 |
        +----------------------------------+     | ipsum|   1 |
                                                 | lorem|   3 |
                                                 | sit  |   5 |
                                                 +------+-----+
        ```python
        SparkWordCountTransformer(
             text_field="value",
             lowercase=True,
             group_by="poem"
         )
        ```

        ```yaml
        transformers:
            - type: SparkWordCountTransformer
              text_field: value
              lowercase: true
              group_by: poem
        ```

        Input DataFrame                                Output DataFrame
        +-------+--------------------------------+     +-------+--------+-----+
        | poem  | value                          |     | poem  | word   |count|
        +-------+--------------------------------+     +-------+--------+-----+
        | hamlet| lorem's ipsum' dolor sit amet  |     | hamlet| amet   |  1  |
        | sonnet| lorem lorem dolor sit sit sit  | ==> | hamlet| dolor  |  1  |
        |       | sit                            |     | hamlet| ipsum' |  1  |
        +------+---------------------------------+     | hamlet| lorem's|  1  |
                                                       | hamlet| sit    |  1  |
                                                       | sonnet| dolor  |  1  |
                                                       | sonnet| lorem  |  2  |
                                                       | sonnet| sit    |  4  |
                                                       +-------+--------+-----+
    """

    def __init__(
        self,
        text_field: str = None,
        lowercase: bool = True,
        group_by: str | list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.text_field = text_field or DEFAULT_SOURCE_COLUMN
        self.lowercase = lowercase
        self.group_by = as_list(group_by, [])

    def transform(self, context: StepContext, data: DataFrame) -> DataFrame:
        tokenize = split(
            lower(self.text_field) if self.lowercase else col(self.text_field),
            TOKEN_DELIMITER_RULE,
        )

        tokens = data.select(
            *self.group_by,
            explode(tokenize).alias(WORD_FIELD),
        )

        grouping_cols = [*self.group_by, WORD_FIELD]

        wordcounts = (
            tokens.groupBy(grouping_cols).count().filter(col(WORD_FIELD) != "").sort(grouping_cols)
        )

        return wordcounts
