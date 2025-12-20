compact_job = dict(
    kind="Job",
    name="test_job",
    org="tiozin",
    region="latam",
    domain="quality",
    product="test_cases",
    model="some_case",
    layer="test",
    runner={
        "kind": "TestRunner",
    },
    inputs={
        "read_something": {
            "kind": "TestInput",
        }
    },
    transforms={
        "transform_something": {
            "kind": "TestTransform",
        }
    },
    outputs={
        "write_something": {
            "kind": "TestOutput",
        }
    },
)


expanded_job = dict(
    kind="Job",
    name="test_job",
    team=None,
    cost_center=None,
    owner=None,
    labels={},
    description=None,
    org="tiozin",
    region="latam",
    domain="quality",
    product="test_cases",
    model="some_case",
    layer="test",
    runner=dict(
        kind="TestRunner",
        streaming=False,
        description=None,
        org=None,
        region=None,
        domain=None,
        product=None,
        model=None,
        layer=None,
    ),
    inputs=dict(
        read_something=dict(
            kind="TestInput",
            description=None,
            org=None,
            region=None,
            domain=None,
            product=None,
            model=None,
            layer=None,
            schema=None,
            schema_subject=None,
            schema_version=None,
        )
    ),
    transforms=dict(
        transform_something=dict(
            kind="TestTransform",
            description=None,
            org=None,
            region=None,
            domain=None,
            product=None,
            model=None,
            layer=None,
        )
    ),
    outputs=dict(
        write_something=dict(
            kind="TestOutput",
            description=None,
            org=None,
            region=None,
            domain=None,
            product=None,
            model=None,
            layer=None,
        )
    ),
)
