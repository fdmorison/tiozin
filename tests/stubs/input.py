from typing import Literal

from tiozin import Context, Input


class InputStub(Input):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_read = None
        self.captured_teardown = None

    def setup(self, context: Context) -> None:
        self.captured_setup = self.path

    def read(self, context: Context) -> Literal["data"]:
        self.captured_read = self.path
        return "data"

    def teardown(self, context: Context) -> None:
        self.captured_teardown = self.path
