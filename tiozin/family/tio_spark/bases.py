from pyspark.sql import DataFrame, SparkSession

from tiozin.api import CoTransform, Input, Output, Transform
from tiozin.assembly import tioproxy
from tiozin.exceptions import NotInitializedError

from .proxy import SparkStepProxy


class SparkStepMixin:
    def __init__(self, **options) -> None:
        super().__init__(**options)

    @property
    def spark(self) -> SparkSession:
        spark = SparkSession.getActiveSession()
        if spark is None:
            raise NotInitializedError(
                "SparkStep requires an active SparkSession. "
                "Make sure the step is executed by a SparkRunner.",
                tiozin=self,
            )
        return spark


@tioproxy(SparkStepProxy)
class SparkInput(SparkStepMixin, Input[DataFrame]):
    pass


@tioproxy(SparkStepProxy)
class SparkTransform(SparkStepMixin, Transform[DataFrame]):
    pass


@tioproxy(SparkStepProxy)
class SparkCoTransform(SparkStepMixin, CoTransform[DataFrame]):
    pass


@tioproxy(SparkStepProxy)
class SparkOutput(SparkStepMixin, Output[DataFrame]):
    pass
