from datetime import datetime

import wrapt
from pyiceberg.catalog import load_catalog
from pyiceberg.table.sorting import NullOrder
from pyiceberg.transforms import IdentityTransform
from typing_extensions import Unpack

from tiozin import Batch, BatchRegistry, BatchStatus
from tiozin.api.conventions import RESOURCE_FIELDS
from tiozin.api.typehint import ResourceKwargs
from tiozin.exceptions import BatchAlreadyExistsError, BatchNotFoundError
from tiozin.utils import default
from tiozin.utils.io import mkdirs

from .... import config
from .dao import IcebergBatchDAO
from .schema import IcebergBatchSchema

MILLIS_PER_DAY = 24 * 60 * 60 * 1000


class IcebergBatchRegistry(BatchRegistry):
    def __init__(
        self,
        location: str = None,
        namespace: str = None,
        table: str = None,
        catalog: str = None,
        catalog_type: str = None,
        retention_days: int = None,
        **options,
    ) -> None:
        super().__init__(location=location, **options)
        self.namespace = default(namespace, config.iceberg_default_namespace)
        self.table = default(table, config.iceberg_default_table)
        self.catalog = default(catalog, config.iceberg_default_catalog)
        self.catalog_type = default(catalog_type, config.iceberg_default_catalog_type)
        self.retention_days = default(
            retention_days, config.iceberg_default_snapshot_retention_days
        )
        self._dao: IcebergBatchDAO = None

    @wrapt.synchronized
    def setup(self) -> None:
        namespace = tuple(self.namespace.split("."))
        table_id = (*namespace, self.table)

        catalog = load_catalog(self.catalog, **self._catalog_properties())
        catalog.create_namespace_if_not_exists(namespace)

        table = catalog.create_table_if_not_exists(
            table_id,
            IcebergBatchSchema,
            properties={
                **config.iceberg_default_table_properties,
                "history.expire.max-snapshot-age-ms": str(self.retention_days * MILLIS_PER_DAY),
            },
        )

        if table.spec().is_unpartitioned():
            with table.transaction() as txn:
                with txn.update_schema() as schema:
                    schema.set_identifier_fields("id")
                with txn.update_spec() as spec:
                    for field in RESOURCE_FIELDS:
                        spec.add_identity(field)
                with txn.update_sort_order() as sort:
                    sort.asc("created_at", IdentityTransform(), NullOrder.NULLS_LAST)

        self._dao = IcebergBatchDAO(table)

    def teardown(self) -> None:
        self._dao.expire_snapshots(self.retention_days)
        self._dao = None

    def _catalog_properties(self) -> dict[str, str]:
        if self.catalog_type == "sqlite":
            mkdirs(self.location)
            return {
                **self.options,
                "type": "sql",
                "uri": f"sqlite:///{self.location}/catalog.db",
                "warehouse": f"file://{self.location}",
            }

        if self.catalog_type == "rest":
            return {
                **self.options,
                "type": self.catalog_type,
                "uri": self.location,
            }

        return {
            **self.options,
            "type": self.catalog_type,
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
