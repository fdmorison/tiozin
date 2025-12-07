from typing import Self

from tio.model.job import Job


class JobBuilder:

    def __init__(self) -> None:
        super().__init__()

    def from_yaml(self, manifest: str) -> Self:
        return self

    def build(self) -> Job:
        return Job()
