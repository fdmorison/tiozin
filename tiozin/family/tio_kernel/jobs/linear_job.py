from tiozin.api import CombineTransform, Context, Job
from tiozin.utils.helpers import as_list


class LinearJob(Job):
    """
    Execute a job using a linear, sequential execution model.

    A LinearJob represents the simplest and most common pipeline shape: data flows forward in a
    single direction, from Inputs through a sequence of Transforms, and finally into one or more
    Outputs.

    Each stage consumes the result of the previous one. Inputs produce the initial datasets,
    Transforms are applied sequentially to evolve the data, and Outputs persist the final result.
    There are no branches or arbitrary dependencies—execution follows a clear, predictable order.

    Pipeline patterns supported by LinearJob include:

    Simple pipeline (single input, single output):
        ┌───────┐    ┌─────────────┐    ┌─────────────┐    ┌────────┐
        │ Input │───►│ Transform 1 │───►│ Transform 2 │───►│ Output │
        └───────┘    └─────────────┘    └─────────────┘    └────────┘

    Multiple inputs (explicitly combined into a single stream):
        ┌─────────┐
        │ Input 1 │───┐
        └─────────┘   │
        ┌─────────┐   │    ┌──────────────────┐    ┌─────────────┐    ┌────────┐
        │ Input 2 │───────►│ CombineTransform │───►│ Transform 2 │───►│ Output │
        └─────────┘   │    └──────────────────┘    └─────────────┘    └────────┘
        ┌─────────┐   │        (join, union, etc.)
        │ Input N │───┘
        └─────────┘

    Multiple outputs (the same transformed data written to different destinations):
        ┌───────┐    ┌─────────────┐    ┌──────────┐
        │ Input │───►│ Transform 1 │───►│ Output 1 │
        └───────┘    └─────────────┘    └──────────┘
                                    ───►│ Output 2 │
                                        └──────────┘
                                    ───►│ Output N │
                                        └──────────┘

    LinearJob intentionally avoids modeling arbitrary DAGs. Its goal is to provide a clear,
    easy-to-reason-about execution model suitable for most ETL workloads. More complex dependency
    graphs may be supported by future implementations.
    """

    def __init__(self, **options) -> None:
        super().__init__(**options)

    def execute(self, context: Context) -> None:
        self.info("The job has started")

        with self.runner:
            # Multiple datasets may be load
            datasets = [input.read(context) for input in self.inputs]
            # Transformers run sequentially
            for t in self.transforms:
                if isinstance(t, CombineTransform):
                    datasets = [t.transform(context, *as_list(datasets))]
                else:
                    datasets = [t.transform(context, d) for d in as_list(datasets)]
            # Each sink saves the same data
            if self.outputs:
                datasets = [output.write(context, *as_list(datasets)) for output in self.outputs]
            # The runner runs each source + transformation + sink combination
            self.runner.execute(context, datasets)

        self.info("The job ran successfully!")

    def teardown(self, **kwargs) -> None:
        self.warning("The job received a stop request.")
        super().teardown(**kwargs)
