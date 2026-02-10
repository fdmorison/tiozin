from typing import Literal

from tiozin import Context, Job


class JobStub(Job):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_submit = None
        self.captured_teardown = None

    def setup(self, context: Context) -> None:
        self.captured_setup = self.path

    def submit(self, context: Context) -> Literal["result"]:
        self.captured_submit = self.path
        return "result"

    def teardown(self, context: Context) -> None:
        self.captured_teardown = self.path
