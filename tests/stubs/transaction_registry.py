from tiozin.api.metadata.transaction.registry import TransactionRegistry


class TransactionRegistryStub(TransactionRegistry):
    def __init__(self):
        super().__init__(location="stub://transaction")

    def get(self, identifier: str = None, version: str = None) -> None:
        return None

    def register(self, identifier: str, value: object) -> None:
        pass
