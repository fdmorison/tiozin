from datetime import timedelta
from functools import reduce

import pyarrow as pa
from pyiceberg.expressions import And, BooleanExpression, EqualTo, Or
from pyiceberg.table import Table

from tiozin.api import State
from tiozin.api.metadata.state.status import StateStatus
from tiozin.utils import default, utcnow

from . import config
from .schema import IcebergStateSchema


class IcebergStateDao:
    def __init__(self, table: Table) -> None:
        self._table = table

    def _where(self, **fields) -> BooleanExpression | None:
        expressions = [EqualTo(field, value) for field, value in fields.items()]
        if not expressions:
            return None
        return reduce(And, expressions)

    def _to_arrow(self, *states: State) -> pa.Table:
        return pa.Table.from_pylist(
            [state.model_dump(mode="python") for state in states],
            schema=IcebergStateSchema.as_arrow(),
        )

    def scan(self, row_filter: BooleanExpression | None = None) -> pa.Table:
        return self._table.scan(row_filter=row_filter).to_arrow()

    def upsert(self, state: State) -> None:
        self._table.upsert(
            df=self._to_arrow(state),
            join_cols=["id"],
        )

    def _to_state(self, row: dict) -> State:
        row["attributes"] = dict(row["attributes"])
        return State(**row)

    def find_latest(self, **fields) -> State | None:
        df = self.scan(self._where(**fields))

        if not len(df):
            return None

        df = df.sort_by([("batch_key", "descending")]).slice(0, 1)
        return self._to_state(df.to_pylist()[0])

    def find_pending(self, **fields) -> list["State"]:
        backlog_statuses = [StateStatus.PENDING, StateStatus.FAILED, StateStatus.RUNNING]
        status_filter = reduce(Or, [EqualTo("status", s) for s in backlog_statuses])
        df = self.scan(And(self._where(**fields), status_filter))
        return [self._to_state(row) for row in df.to_pylist()]

    def expire_snapshots(self, days: int = None) -> None:
        days = default(days, config.default_snapshot_retention_days)
        date = utcnow() - timedelta(days=days)
        self._table.maintenance.expire_snapshots().older_than(date).commit()
