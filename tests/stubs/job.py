from __future__ import annotations

from typing import Literal

from wrapt import ObjectProxy

from tiozin import Context, Job


class JobStub(Job):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = "./data/{{domain}}/{{layer}}"
        self.captured_setup = None
        self.captured_submit = None
        self.captured_teardown = None
        self.captured_backlogs = []
        self.submit_count = 0
        self.failure = None

    def setup(self) -> None:
        self.captured_setup = self.path

    def submit(self) -> Literal["result"]:
        self.submit_count += 1
        self.captured_submit = self.path
        self.captured_backlogs.append(Context.current().get_job_backlog())
        if self.failure is not None:
            raise self.failure
        return "result"

    def teardown(self) -> None:
        self.captured_teardown = self.path

    def unwrap(self) -> JobStub:
        job = self
        while isinstance(job, ObjectProxy):
            job = job.__wrapped__
        return job
