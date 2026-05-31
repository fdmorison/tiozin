# Output

**Must implement:** `write(self, data: TData) -> Any`

**Optional overrides:**
- `setup(self) -> None`: called before the first `write()`
- `teardown(self) -> None`: called after the last `write()`
- `external_datasets(self) -> Datasets`: declares lineage when accessing external infra

```python
from tiozin import Output, Dataset, Datasets
from tiozin.exceptions import RequiredArgumentError


class AcmeOutput(Output):
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
            outputs=[
                Dataset.postgres(
                    self.host,
                    5432,
                    self.database,
                    "public",
                    self.table,
                ),
            ]
        )

    def write(self, data: list[dict]) -> None:
        AcmeClient(host=self.host, database=self.database).push(self.table, data)
```
