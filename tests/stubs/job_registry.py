from tiozin import JobManifest, JobRegistry


class JobRegistryStub(JobRegistry):
    def __init__(self):
        super().__init__(location="stub://job")

    def get(self, identifier: str) -> JobManifest:
        return None

    def register(self, identifier: str, value: JobManifest) -> None:
        pass
