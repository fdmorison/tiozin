from datetime import datetime, timedelta
from functools import reduce

import pyarrow as pa
import pyarrow.compute as pc
from pyiceberg.expressions import (
    And,
    BooleanExpression,
    EqualTo,
    GreaterThanOrEqual,
    In,
    NotEqualTo,
)
from pyiceberg.table import Table

from tiozin import Batch, BatchStatus
from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.utils import dumps_json, loads_json, utcnow

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
        return self._to_object(df)

    def find_frontier(self, **fields) -> Batch | None:
        df = self._scan(NotEqualTo("status", BatchStatus.CANCELED), **fields)

        if not len(df):
            return None

        max_created_at = pc.max(df["created_at"]).as_py()
        df = df.filter(pc.equal(df["created_at"], max_created_at)).slice(0, 1)
        return self._to_object(df)

    def find_by_status(self, *statuses: BatchStatus, **fields) -> list[Batch]:
        df = self._scan(
            In("status", statuses),
            **fields,
        )
        return self._to_objects(df)

    def find_board(self, limit: int, since: datetime, **fields) -> list[Batch]:
        df = (
            self._scan(GreaterThanOrEqual("created_at", since), **fields)
            .sort_by([("created_at", "descending")])
            .slice(0, limit)
        )
        return self._to_objects(df)

    def expire_snapshots(self, days: int) -> None:
        date = utcnow() - timedelta(days=days)
        self._table.maintenance.expire_snapshots().older_than(date).commit()

    def _to_object(self, df: pa.Table) -> Batch | None:
        if not len(df):
            return None
        row = df.to_pylist(maps_as_pydicts="strict")[0]
        row["attributes"] = loads_json(row["attributes"])
        return Batch(**row)

    def _to_objects(self, df: pa.Table) -> list[Batch]:
        batches = []
        for row in df.to_pylist(maps_as_pydicts="strict"):
            row["attributes"] = loads_json(row["attributes"])
            batches.append(Batch(**row))
        return batches

    def _to_arrow(self, batch: Batch) -> pa.Table:
        record = batch.model_dump(mode="python")
        record["attributes"] = dumps_json(record["attributes"])

        return pa.Table.from_pylist([record], schema=self._table.schema().as_arrow())

    def _scan(self, *expressions: BooleanExpression, **fields) -> pa.Table:
        filters = [EqualTo(f, v) for f, v in fields.items()] + list(expressions)
        row_filter = reduce(And, filters) if filters else None
        return self._table.scan(row_filter=row_filter).to_arrow()
