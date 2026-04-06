from typing import Any

from tiozin import Dataset, Datasets, Transform


class TransformStub(Transform):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_transform = None
        self.captured_teardown = None

    def setup(self) -> None:
        self.captured_setup = self.path

    def transform(self, data) -> Any:
        self.captured_transform = self.path
        return data

    def teardown(self) -> None:
        self.captured_teardown = self.path

    def external_datasets(self) -> Datasets:
        return Datasets(
            inputs=[Dataset.from_uri(self.path)],
            outputs=[Dataset.from_uri(self.path)],
        )
