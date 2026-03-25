from typing import Literal

from tiozin import Input, Lineage, LineageDataset


class InputStub(Input):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_read = None
        self.captured_teardown = None

    def setup(self) -> None:
        self.captured_setup = self.path

    def read(self) -> Literal["data"]:
        self.captured_read = self.path
        return "data"

    def teardown(self) -> None:
        self.captured_teardown = self.path

    def lineage_datasets(self) -> Lineage:
        return Lineage(
            inputs=[LineageDataset.from_uri(self.path)],
            outputs=[],
        )
