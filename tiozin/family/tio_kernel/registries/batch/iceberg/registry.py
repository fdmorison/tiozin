from datetime import datetime

import wrapt
from pyiceberg.catalog import load_catalog
from typing_extensions import Unpack

from tiozin import Batch, BatchRegistry, BatchStatus
from tiozin.api.typehint import ResourceKwargs
from tiozin.exceptions import BatchAlreadyExistsError, BatchNotFoundError
from tiozin.utils import default

from .... import config
from .catalogs import IcebergCatalogFactory
from .dao import IcebergBatchDAO
from .schema import IcebergBatchSchema
from .utils import create_table_if_not_exists


class IcebergBatchRegistry(BatchRegistry):
    """
    Batch registry backed by an Apache Iceberg table.

    Persists each batch as a row in an Iceberg table, partitioned by the
    resource fields so concurrent jobs do not contend for the same files, and
    uniquely identified by `id`. On setup, the database and table are created
    when absent. On teardown, snapshots older than the retention window are
    expired.

    The catalog is resolved from `catalog_type`, with dedicated handling for
    the "sqlite" and "rest" backends and passthrough for any other type
    supported by PyIceberg.

    Attributes:
        database:
            Dot-separated Iceberg namespace that holds the batch table.
        table:
            Name of the Iceberg table that stores batches.
        catalog:
            Name of the Iceberg catalog to load.
        catalog_type:
            Backend type of the catalog, such as "sqlite" or "rest".
        retention_days:
            Number of days a snapshot is kept before it becomes eligible for
            expiry.
        options:
            Extra catalog properties forwarded to PyIceberg when the catalog is
            loaded.
    """

    def __init__(
        self,
        location: str = None,
        database: str = None,
        table: str = None,
        catalog: str = None,
        catalog_type: str = None,
        retention_days: int = None,
        **options,
    ) -> None:
        super().__init__(location=location, **options)
        self.database = default(database, config.iceberg_default_database)
        self.table = default(table, config.iceberg_default_table)
        self.catalog = default(catalog, config.iceberg_default_catalog)
        self.catalog_type = default(catalog_type, config.iceberg_default_catalog_type)
        self.retention_days = default(
            retention_days, config.iceberg_default_snapshot_retention_days
        )
        self._batch_dao: IcebergBatchDAO = None

    @wrapt.synchronized
    def setup(self) -> None:
        database = tuple(self.database.split("."))
        qualified_table = (*database, self.table)

        properties = IcebergCatalogFactory.build(self.catalog_type, self.location, **self.options)
        catalog = load_catalog(self.catalog, **properties)
        catalog.create_namespace_if_not_exists(database)

        table = create_table_if_not_exists(
            catalog,
            qualified_table,
            IcebergBatchSchema,
            self.retention_days,
        )

        self._batch_dao = IcebergBatchDAO(table)

    def teardown(self) -> None:
        self._batch_dao.expire_snapshots(self.retention_days)
        self._batch_dao = None

    def register(self, batch: Batch) -> Batch:
        if self._batch_dao.insert(batch) == 0:
            raise BatchAlreadyExistsError(batch=batch)
        return batch

    def register_transition(self, batch: Batch) -> Batch:
        if self._batch_dao.update(batch) == 0:
            raise BatchNotFoundError(batch=batch)
        return batch

    def get(self, id: str, **resource: Unpack[ResourceKwargs]) -> Batch:
        batch = self._batch_dao.find(id=id, **resource)
        if not batch:
            raise BatchNotFoundError(batch=id)
        return batch

    def get_frontier(self, **resource: Unpack[ResourceKwargs]) -> Batch | None:
        return self._batch_dao.find_frontier(**resource)

    def get_backlog(self, **resource: Unpack[ResourceKwargs]) -> list[Batch]:
        return self._batch_dao.find_by_status(
            BatchStatus.PENDING,
            BatchStatus.FAILED,
            BatchStatus.RUNNING,
            **resource,
        )

    def get_board(
        self, limit: int, since: datetime, **resource: Unpack[ResourceKwargs]
    ) -> list[Batch]:
        return self._batch_dao.find_board(limit, since, **resource)
