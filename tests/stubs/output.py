from typing import Any

from tiozin import Context, Output


class OutputStub(Output):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_write = None
        self.captured_teardown = None

    def setup(self, context: Context, data: Any) -> None:
        self.captured_setup = self.path

    def write(self, context: Context, data: Any) -> None:
        self.captured_write = self.path
        return data

    def teardown(self, context: Context, data: Any) -> None:
        self.captured_teardown = self.path
