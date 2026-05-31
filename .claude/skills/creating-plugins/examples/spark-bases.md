# Convenience bases from tio_spark

When adding a plugin to the `tio_spark` family, use its convenience bases instead of the core ones. They add `self.spark` (`SparkSession`) to every lifecycle method.

```python
from pyspark.sql import DataFrame

from tiozin.family.tio_spark import SparkTransform


class AcmeSparkTransform(SparkTransform):
    def __init__(self, query: str = None, **options) -> None:
        super().__init__(**options)
        self.query = query

    def transform(self, data: DataFrame) -> DataFrame:
        data.createOrReplaceTempView("data")
        return self.spark.sql(self.query)
```
