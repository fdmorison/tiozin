# Convenience bases from tio_duckdb

When adding a plugin to the `tio_duckdb` family, use its convenience bases instead of the core ones. They add `self.duckdb` (`DuckDBPyConnection`) and helpers:
- `self.fetch(query, parameters)`: executes query and returns `list[dict]`
- `self.scriptfy(*statements)`: joins SQL strings with semicolons

```python
from duckdb import DuckDBPyRelation

from tiozin.family.tio_duckdb import DuckdbTransform


class AcmeDuckdbTransform(DuckdbTransform):
    def __init__(self, column: str = None, **options) -> None:
        super().__init__(**options)
        self.column = column

    def transform(self, data: DuckDBPyRelation) -> DuckDBPyRelation:
        return self.duckdb.sql(f"""
            SELECT {self.column}, COUNT(*) AS count
            FROM {data.alias}
            GROUP BY 1
            ORDER BY count DESC
        """)
```
