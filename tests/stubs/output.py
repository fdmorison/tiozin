from typing import Any

from tiozin import Output


class OutputStub(Output):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_write = None
        self.captured_teardown = None

    def setup(self, data: Any) -> None:
        self.captured_setup = self.path

    def write(self, data: Any) -> None:
        self.captured_write = self.path
        return data

    def teardown(self, data: Any) -> None:
        self.captured_teardown = self.path
