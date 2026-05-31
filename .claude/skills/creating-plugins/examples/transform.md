# Transform

## Transform (single input)

**Must implement:** `transform(self, data: TData) -> TData`

**Optional overrides:**
- `setup(self) -> None`: called before the first `transform()`
- `teardown(self) -> None`: called after the last `transform()`
- `external_datasets(self) -> Datasets`: declares lineage when accessing external infra

```python
from tiozin import Transform


class AcmeTransform(Transform):
    def __init__(self, column: str = None, **options) -> None:
        super().__init__(**options)
        self.column = column

    def transform(self, data: list[dict]) -> list[dict]:
        total = sum(row[self.column] for row in data)
        return [{"column": self.column, "total": total}]
```

## Transform with external datasets

When a Transform reads from an external system, declare `external_datasets`.

```python
from tiozin import Dataset, Datasets, Transform
from tiozin.exceptions import RequiredArgumentError


class AcmeLookupTransform(Transform):
    def __init__(
        self, host: str = None, database: str = None, table: str = None, **options
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            host=host,
            database=database,
            table=table,
        )
        self.host = host
        self.database = database
        self.table = table

    def external_datasets(self) -> Datasets:
        return Datasets(
            inputs=[
                Dataset.postgres(
                    self.host,
                    5432,
                    self.database,
                    "public",
                    self.table,
                ),
            ]
        )

    def transform(self, data: list[dict]) -> list[dict]:
        lookup = {
            row["id"]: row
            for row in AcmeClient(host=self.host, database=self.database).fetch(self.table)
        }
        return [{**row, **lookup.get(row["id"], {})} for row in data]
```

## CoTransform (multiple inputs)

**Must implement:** `transform(self, data: TData, *others: TData) -> TData`

`data` is the primary input; `others` are additional inputs joined in declaration order.

```python
from tiozin import CoTransform


class AcmeCoTransform(CoTransform):
    def __init__(self, **options) -> None:
        super().__init__(**options)

    def transform(self, data: list[dict], *others: list[dict]) -> list[dict]:
        return [*data, *(row for group in others for row in group)]
```
