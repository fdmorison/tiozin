# Runner

**Must implement:**
- `session` property: active compute session (e.g., `DuckDBPyConnection`, `SparkSession`)
- `setup(self) -> None`: initialize the session
- `run(self, execution_plan: TPlan, **options) -> TOutput`: execute the plan
- `teardown(self) -> None`: release the session

```python
from tiozin import Runner


class AcmeRunner(Runner):
    def __init__(self, **options) -> None:
        super().__init__(**options)
        self._session = None

    @property
    def session(self):
        return self._session

    def setup(self) -> None:
        self._session = AcmeSession()
        self.info("Session ready")

    def run(self, execution_plan, **options):
        ...

    def teardown(self) -> None:
        if self._session:
            self._session.close()
        self._session = None
        self.info("Session closed")
```
