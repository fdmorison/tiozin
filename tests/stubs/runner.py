from tiozin.api.processors.runner import Runner


class StubRunner(Runner):
    @property
    def session(self) -> None:
        return None

    def setup(self, context) -> None:
        pass

    def run(self, context, execution_plan, **options) -> None:
        pass

    def teardown(self, context) -> None:
        pass
