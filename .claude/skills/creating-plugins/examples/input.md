# Input

**Must implement:** `read(self) -> TData`

**Optional overrides:**
- `setup(self) -> None`: called before the first `read()`
- `teardown(self) -> None`: called after the last `read()`
- `external_datasets(self) -> Datasets`: declares lineage when accessing external infra

```python
from tiozin import Input, Dataset, Datasets
from tiozin.exceptions import RequiredArgumentError


class AcmeInput(Input):
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

    def read(self) -> list[dict]:
        return AcmeClient(host=self.host, database=self.database).fetch(self.table)
```
