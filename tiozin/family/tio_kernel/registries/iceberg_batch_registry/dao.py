from datetime import timedelta
from functools import reduce

import pyarrow as pa
import pyarrow.compute as pc
from pyiceberg.expressions import And, BooleanExpression, EqualTo, In
from pyiceberg.table import Table

from tiozin import Batch, BatchStatus
from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.exceptions import BatchAlreadyExistsError, BatchNotFoundError
from tiozin.utils import default, utcnow

from . import config
from .schema import IcebergBatchSchema

NATURAL_KEY_FIELDS = (*RESOURCE_FIELDS, "nominal_time")


class IcebergBatchDAO:
    def __init__(self, table: Table) -> None:
        self._table = table

    def _to_arrow(self, *states: Batch) -> pa.Table:
        return pa.Table.from_pylist(
            [state.model_dump(mode="python") for state in states],
            schema=IcebergBatchSchema.as_arrow(),
        )

    def _to_state(self, row: dict) -> Batch:
        row["attributes"] = dict(row["attributes"])
        return Batch(**row)

    def _scan(self, *expressions: BooleanExpression, **fields) -> pa.Table:
        filters = [EqualTo(f, v) for f, v in fields.items()] + list(expressions)
        row_filter = reduce(And, filters) if filters else None
        return self._table.scan(row_filter=row_filter).to_arrow()

    def insert(self, state: Batch) -> None:
        result = self._table.upsert(
            df=self._to_arrow(state),
            join_cols=list(NATURAL_KEY_FIELDS),
            when_matched_update_all=False,
        )
        if result.rows_inserted == 0:
            raise BatchAlreadyExistsError(state=state)

    def update(self, state: Batch) -> None:
        result = self._table.upsert(
            df=self._to_arrow(state),
            join_cols=list(NATURAL_KEY_FIELDS),
            when_not_matched_insert_all=False,
        )
        if result.rows_updated == 0:
            raise BatchNotFoundError(state=state)

    def upsert(self, state: Batch) -> None:
        self._table.upsert(
            df=self._to_arrow(state),
            join_cols=list(NATURAL_KEY_FIELDS),
        )

    def find_all(self, **fields) -> list[Batch]:
        return [self._to_state(row) for row in self._scan(**fields).to_pylist()]

    def find_latest(self, **fields) -> Batch | None:
        df = self._scan(**fields)

        if not len(df):
            return None

        max_created_at = pc.max(df["created_at"]).as_py()
        row = df.filter(pc.equal(df["created_at"], max_created_at)).slice(0, 1)
        return self._to_state(row.to_pylist()[0])

    def find_by_status(self, *statuses: BatchStatus, **fields) -> list[Batch]:
        df = self._scan(
            In("status", statuses),
            **fields,
        )
        return [self._to_state(row) for row in df.to_pylist()]

    def find_history(self, limit: int, **fields) -> list[Batch]:
        df = self._scan(**fields).sort_by([("created_at", "descending")]).slice(0, limit)
        return [self._to_state(row) for row in df.to_pylist()]

    def expire_snapshots(self, days: int = None) -> None:
        days = default(days, config.default_snapshot_retention_days)
        date = utcnow() - timedelta(days=days)
        self._table.maintenance.expire_snapshots().older_than(date).commit()
