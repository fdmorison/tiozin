from unittest.mock import MagicMock

from tiozin.assembly.registry_factory import RegistryFactory


class MockedRegistryFactory:
    def __init__(self) -> None:
        self.lineage_registry = MagicMock(name="lineage", spec=RegistryFactory)
        self.metric_registry = MagicMock(name="metric", spec=RegistryFactory)
        self.schema_registry = MagicMock(name="schema", spec=RegistryFactory)
        self.secret_registry = MagicMock(name="secret", spec=RegistryFactory)
        self.transaction_registry = MagicMock(name="transaction", spec=RegistryFactory)
        self.job_registry = MagicMock(name="job_registry", spec=RegistryFactory)

    def all_registries(self) -> list[MagicMock]:
        return [
            self.lineage_registry,
            self.metric_registry,
            self.schema_registry,
            self.secret_registry,
            self.transaction_registry,
            self.job_registry,
        ]
