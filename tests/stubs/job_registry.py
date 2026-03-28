from tiozin.api.metadata.job.model import JobManifest
from tiozin.api.metadata.job.registry import JobRegistry


class JobRegistryStub(JobRegistry):
    def __init__(self):
        super().__init__(location="stub://job")

    def get(self, identifier: str = None, version: str = None) -> JobManifest:
        return None

    def register(self, identifier: str, value: JobManifest) -> None:
        pass
