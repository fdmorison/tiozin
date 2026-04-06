from typing import Any

from tiozin import Dataset, Datasets, Output


class OutputStub(Output):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_write = None
        self.captured_teardown = None

    def setup(self) -> None:
        self.captured_setup = self.path

    def write(self, data: Any) -> None:
        self.captured_write = self.path
        return data

    def teardown(self) -> None:
        self.captured_teardown = self.path

    def external_datasets(self) -> Datasets:
        return Datasets(
            outputs=[Dataset.from_uri(self.path)],
        )
