# Lineage

## Job lineage

Every job has a namespace that identifies it in the lineage graph. By default it is derived from the job's taxonomy using the template `{{org}}.{{region}}.{{domain}}.{{subdomain}}`. Set it explicitly in the YAML to override:

```yaml
kind: LinearJob
name: sqlite_orders_etl
namespace: acme.latam.ecommerce.checkout
```

Or change the default globally with `TIO_JOB_NAMESPACE_TEMPLATE`:

```bash
TIO_JOB_NAMESPACE_TEMPLATE="{{org}}.{{domain}}"
```

The job namespace is always logical. It represents where the job fits in your organization, not where the data lives. `acme.latam.ecommerce.checkout` is a domain address, not a system address.

## Dataset lineage

Override `lineage_datasets()` on your Input or Output to report the physical dataset it touches:

```python
from tiozin import Lineage, LineageDataset


class SQLiteOutput(Output[str]):
    def __init__(self, table: str, **options) -> None:
        super().__init__(**options)
        self.table = table

    def write(self, data: str) -> SQLiteWriteSpec:
        sql = f"CREATE TABLE IF NOT EXISTS {self.table} AS {data}"
        return SQLiteWriteSpec(sql=sql)

    def lineage_datasets(self) -> Lineage:
        return Lineage(
            inputs=[],
            outputs=[LineageDataset(namespace="sqlite", name=self.table)],
        )
```

If you skip it, the framework falls back to a logical dataset derived from the job's taxonomy. Good enough for development, but it does not point to a real system.

The dataset namespace is always infrastructure. It points to the system where the data physically lives: `postgres://host:5432`, `kafka://broker:9092`, `s3://my-bucket`, `bigquery`. Follow the [OpenLineage naming spec](https://openlineage.io/docs/spec/naming/) for the exact format per backend. The `name` identifies the dataset within that system: a table, a topic, a path.
