import json
from datetime import datetime, timedelta
from functools import reduce

import pyarrow as pa
import pyarrow.compute as pc
from pyiceberg.expressions import And, BooleanExpression, EqualTo, GreaterThanOrEqual, In
from pyiceberg.table import Table

from tiozin import Batch, BatchStatus
from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.utils import prune, utcnow

NATURAL_KEY_FIELDS = (*RESOURCE_FIELDS, "nominal_time")


class IcebergBatchDAO:
    def __init__(self, table: Table) -> None:
        self._table = table

    def insert(self, batch: Batch) -> int:
        result = self._table.upsert(
            df=self._to_arrow(batch),
            join_cols=list(NATURAL_KEY_FIELDS),
            when_matched_update_all=False,
        )
        return result.rows_inserted

    def update(self, batch: Batch) -> int:
        result = self._table.upsert(
            df=self._to_arrow(batch),
            join_cols=[*RESOURCE_FIELDS, "id"],
            when_not_matched_insert_all=False,
        )
        return result.rows_updated

    def find(self, id: str, **fields) -> Batch | None:
        df = self._scan(id=id, **fields)
        return self._to_batch(df)

    def find_latest(self, **fields) -> Batch | None:
        df = self._scan(**fields)

        if not len(df):
            return None

        max_created_at = pc.max(df["created_at"]).as_py()
        df = df.filter(pc.equal(df["created_at"], max_created_at)).slice(0, 1)
        return self._to_batch(df)

    def find_by_status(self, *statuses: BatchStatus, **fields) -> list[Batch]:
        df = self._scan(
            In("status", statuses),
            **fields,
        )
        return self._to_batches(df)

    def find_history(self, limit: int, since: datetime, **fields) -> list[Batch]:
        df = (
            self._scan(GreaterThanOrEqual("created_at", since), **fields)
            .sort_by([("created_at", "descending")])
            .slice(0, limit)
        )
        return self._to_batches(df)

    def expire_snapshots(self, days: int) -> None:
        date = utcnow() - timedelta(days=days)
        self._table.maintenance.expire_snapshots().older_than(date).commit()

    def _to_batch(self, df: pa.Table) -> Batch | None:
        if not len(df):
            return None
        row = df.to_pylist()[0]
        row["attributes"] = json.loads(row["attributes"])
        return Batch(**row)

    def _to_batches(self, df: pa.Table) -> list[Batch]:
        batches = []
        for row in df.to_pylist():
            row["attributes"] = json.loads(row["attributes"])
            batches.append(Batch(**row))
        return batches

    def _to_arrow(self, batch: Batch) -> pa.Table:
        record = batch.model_dump(mode="python")
        record["attributes"] = json.dumps(record["attributes"])

        with self._table.update_schema() as update:
            # Avoid Arrow inferring `null` types.
            sample = prune(record, dicts=True, lists=True)
            # Infer newly inferred fields.
            inferred_schema = pa.Table.from_pylist([sample]).schema
            inferred_schema = inferred_schema.set(
                inferred_schema.get_field_index("id"),
                inferred_schema.field("id").with_nullable(False),
            )
            update.union_by_name(inferred_schema)

        return pa.Table.from_pylist([record], schema=self._table.schema().as_arrow())

    def _scan(self, *expressions: BooleanExpression, **fields) -> pa.Table:
        filters = [EqualTo(f, v) for f, v in fields.items()] + list(expressions)
        row_filter = reduce(And, filters) if filters else None
        return self._table.scan(row_filter=row_filter).to_arrow()
