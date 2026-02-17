from typing import Any

from tiozin import Runner


class RunnerStub(Runner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_run = None
        self.captured_teardown = None
        self._session = None

    @property
    def session(self) -> Any:
        return self._session

    def setup(self) -> None:
        self.captured_setup = self.path

    def run(self, execution_plan: str, **options) -> None:
        self.captured_run = self.path

    def teardown(self) -> None:
        self.captured_teardown = self.path
