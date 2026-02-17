from typing import Any

from tiozin import Transform


class TransformStub(Transform):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_transform = None
        self.captured_teardown = None

    def setup(self, data: Any) -> None:
        self.captured_setup = self.path

    def transform(self, data) -> Any:
        self.captured_transform = self.path
        return data

    def teardown(self, data: Any) -> None:
        self.captured_teardown = self.path
