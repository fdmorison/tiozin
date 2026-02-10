from typing import Any

from tiozin import Context, Transform


class StubTransform(Transform):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_transform = None
        self.captured_teardown = None

    def setup(self, context: Context, data: Any) -> None:
        self.captured_setup = self.path

    def transform(self, context: Context, data) -> Any:
        self.captured_transform = self.path
        return data

    def teardown(self, context: Context, data: Any) -> None:
        self.captured_teardown = self.path
