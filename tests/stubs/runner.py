from tiozin import Context, Runner


class RunnerStub(Runner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_run = None
        self.captured_teardown = None

    @property
    def session(self) -> None:
        return {}

    def setup(self, context: Context) -> None:
        self.captured_setup = self.path

    def run(self, context: Context, execution_plan: str, **options) -> None:
        self.captured_run = self.path

    def teardown(self, context: Context) -> None:
        self.captured_teardown = self.path
