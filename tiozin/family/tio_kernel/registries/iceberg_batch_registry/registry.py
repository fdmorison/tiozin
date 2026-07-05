from datetime import datetime

import wrapt
from pyiceberg.catalog import load_catalog
from pyiceberg.table.sorting import NullOrder, SortDirection, SortField, SortOrder
from typing_extensions import Unpack

from tiozin import BatchStatus
from tiozin.api import Batch, BatchRegistry
from tiozin.api.typehint import ResourceKwargs
from tiozin.exceptions import BatchAlreadyExistsError, BatchNotFoundError
from tiozin.utils import default
from tiozin.utils.io import mkdirs

from . import config
from .dao import IcebergBatchDAO
from .schema import CREATED_AT_INDEX, IcebergBatchPartitionSpec, IcebergBatchSchema

MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000


class IcebergBatchRegistry(BatchRegistry):
    def __init__(
        self,
        location: str = None,
        namespace: str = None,
        table_name: str = None,
        catalog_name: str = None,
        catalog_type: str = None,
        retention_days: int = None,
        **options,
    ) -> None:
        super().__init__(location=location, **options)
        self.namespace = default(namespace, config.default_namespace)
        self.table_name = default(table_name, config.default_table_name)
        self.catalog_name = default(catalog_name, config.default_catalog_name)
        self.catalog_type = default(catalog_type, config.default_catalog_type)
        self.retention_days = default(retention_days, config.default_snapshot_retention_days)
        self._dao: IcebergBatchDAO = None

    @wrapt.synchronized
    def setup(self) -> None:
        namespace = tuple(self.namespace.split("."))
        table_id = (*namespace, self.table_name)

        catalog = load_catalog(self.catalog_name, **self._catalog_properties())
        catalog.create_namespace_if_not_exists(namespace)

        table = catalog.create_table_if_not_exists(
            table_id,
            schema=IcebergBatchSchema,
            partition_spec=IcebergBatchPartitionSpec,
            sort_order=SortOrder(
                SortField(
                    source_id=CREATED_AT_INDEX,
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

        self._dao = IcebergBatchDAO(table)

    def teardown(self) -> None:
        self._dao.expire_snapshots(self.retention_days)
        self._dao = None

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

    def register(self, batch: Batch) -> Batch:
        if self._dao.insert(batch) == 0:
            raise BatchAlreadyExistsError(batch=batch)
        return batch

    def begin(self, batch: Batch) -> Batch:
        if self._dao.update(batch) == 0:
            raise BatchNotFoundError(batch=batch)
        return batch

    def commit(self, batch: Batch) -> Batch:
        if self._dao.update(batch) == 0:
            raise BatchNotFoundError(batch=batch)
        return batch

    def fail(self, batch: Batch) -> Batch:
        if self._dao.update(batch) == 0:
            raise BatchNotFoundError(batch=batch)
        return batch

    def cancel(self, batch: Batch) -> Batch:
        if self._dao.update(batch) == 0:
            raise BatchNotFoundError(batch=batch)
        return batch

    def quarantine(self, batch: Batch) -> Batch:
        if self._dao.update(batch) == 0:
            raise BatchNotFoundError(batch=batch)
        return batch

    def replay(self, batch: Batch) -> Batch:
        if self._dao.update(batch) == 0:
            raise BatchNotFoundError(batch=batch)
        return batch

    def get(self, id: str, **resource: Unpack[ResourceKwargs]) -> Batch:
        batch = self._dao.find(id=id, **resource)
        if not batch:
            raise BatchNotFoundError(batch=id)
        return batch

    def get_latest(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        return self._dao.find_latest(**resource)

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        return self._dao.find_by_status(
            BatchStatus.PENDING,
            BatchStatus.FAILED,
            BatchStatus.RUNNING,
            **resource,
        )

    def get_history(
        self, limit: int, since: datetime, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        return self._dao.find_history(limit, since, **resource)
