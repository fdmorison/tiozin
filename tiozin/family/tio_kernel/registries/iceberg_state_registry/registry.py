import wrapt
from pyiceberg.catalog import load_catalog
from pyiceberg.partitioning import PartitionField
from pyiceberg.table import PartitionSpec
from pyiceberg.table.sorting import NullOrder, SortDirection, SortField, SortOrder
from pyiceberg.transforms import IdentityTransform
from typing_extensions import Unpack

from tiozin.api import State, StateRegistry
from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.api.metadata.state.exceptions import StateAlreadyExistsError, StateNotFoundError
from tiozin.api.metadata.state.status import BatchStatus
from tiozin.api.typehint import ResourceKwargs
from tiozin.utils import default
from tiozin.utils.io import mkdirs

from . import config
from .dao import IcebergStateDao
from .schema import IcebergStateSchema

MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000

BACKLOG_STATUSES = (BatchStatus.PENDING, BatchStatus.RUNNING, BatchStatus.FAILED)


class IcebergStateRegistry(StateRegistry):
    def __init__(
        self,
        location: str = None,
        namespace: str = None,
        table_name: str = None,
        catalog_name: str = None,
        catalog_type: str = None,
        retention_days: int = None,
        retries: int = None,
        **options,
    ) -> None:
        super().__init__(location=location, retries=retries, **options)
        self.namespace = default(namespace, config.default_namespace)
        self.table_name = default(table_name, config.default_table_name)
        self.catalog_name = default(catalog_name, config.default_catalog_name)
        self.catalog_type = default(catalog_type, config.default_catalog_type)
        self.retention_days = default(retention_days, config.default_snapshot_retention_days)
        self._dao: IcebergStateDao = None

    def teardown(self) -> None:
        self._dao.expire_snapshots(self.retention_days)
        self._dao = None

    @wrapt.synchronized
    def setup(self) -> None:
        namespace = tuple(self.namespace.split("."))
        table_id = (*namespace, self.table_name)

        catalog = load_catalog(self.catalog_name, **self._catalog_properties())
        catalog.create_namespace_if_not_exists(namespace)

        table = catalog.create_table_if_not_exists(
            table_id,
            schema=IcebergStateSchema,
            partition_spec=PartitionSpec(
                *(
                    PartitionField(i, 1000 + i - 2, IdentityTransform(), field)
                    for i, field in enumerate(RESOURCE_FIELDS, start=2)
                )
            ),
            sort_order=SortOrder(
                SortField(
                    source_id=9,
                    direction=SortDirection.ASC,
                    null_order=NullOrder.NULLS_LAST,
                ),
            ),
            properties={
                "format-version": config.table_format_version,
                "history.expire.max-snapshot-age-ms": str(
                    self.retention_days * MILLISECONDS_PER_DAY
                ),
                "history.expire.min-snapshots-to-keep": config.table_min_snapshots_to_keep,
            },
        )

        self._dao = IcebergStateDao(table)

    def _catalog_properties(self) -> dict[str, str]:
        if self.catalog_type == "sql":
            mkdirs(self.location)
            return {
                **self.options,
                "type": "sql",
                "uri": f"sqlite:///{self.location}/catalog.db",
                "warehouse": f"file://{self.location}",
            }

        if self.catalog_type in {"filesystem", "hadoop"}:
            return {
                **self.options,
                "type": self.catalog_type,
                "warehouse": f"file://{self.location}",
            }

        return {
            **self.options,
            "type": self.catalog_type,
            "uri": self.location,
        }

    def register(self, state: State) -> State:
        if not self._dao.create(state):
            raise StateAlreadyExistsError(state=state)
        return state

    def begin(self, state: State) -> State:
        state.status = state.status.to_running()
        if not self._dao.update(state):
            raise StateNotFoundError(state=state)
        return state

    def commit(self, state: State) -> State:
        state.status = state.status.to_succeeded()
        if not self._dao.update(state):
            raise StateNotFoundError(state=state)
        return state

    def fail(self, state: State) -> State:
        state.status = state.status.to_failed()
        if not self._dao.update(state):
            raise StateNotFoundError(state=state)
        return state

    def cancel(self, state: State) -> State:
        state.status = state.status.to_canceled()
        if not self._dao.update(state):
            raise StateNotFoundError(state=state)
        return state

    def quarantine(self, state: State) -> State:
        state.status = state.status.to_quarantined()
        if not self._dao.update(state):
            raise StateNotFoundError(state=state)
        return state

    def replay(self, state: State) -> State:
        state.status = state.status.to_pending()
        if not self._dao.update(state):
            raise StateNotFoundError(state=state)
        return state

    def get_watermark(self, **resource: Unpack[ResourceKwargs]) -> State | None:
        return self._dao.find_latest(**resource)

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[State]:
        return self._dao.find_by_status(*BACKLOG_STATUSES, **resource)
