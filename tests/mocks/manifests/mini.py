job = dict(
    kind="Job",
    name="test_job",
    org="tiozin",
    region="latam",
    domain="quality",
    subdomain="pipeline",
    layer="test",
    product="test_cases",
    model="some_case",
    runner={
        "kind": "TestRunner",
    },
    inputs=[
        {
            "kind": "TestInput",
            "name": "read_something",
        }
    ],
    transforms=[
        {
            "kind": "TestTransform",
            "name": "transform_something",
        }
    ],
    outputs=[
        {
            "kind": "TestOutput",
            "name": "write_something",
        }
    ],
)


expanded_job = dict(
    kind="Job",
    name="test_job",
    description=None,
    maintainer=None,
    cost_center=None,
    owner=None,
    labels={},
    org="tiozin",
    region="latam",
    domain="quality",
    subdomain="pipeline",
    layer="test",
    product="test_cases",
    model="some_case",
    runner=dict(
        kind="TestRunner",
        name=None,
        streaming=False,
        description=None,
    ),
    inputs=[
        dict(
            kind="TestInput",
            name="read_something",
            description=None,
            org=None,
            region=None,
            domain=None,
            subdomain=None,
            layer=None,
            product=None,
            model=None,
            schema=None,
            schema_subject=None,
            schema_version=None,
        )
    ],
    transforms=[
        dict(
            kind="TestTransform",
            name="transform_something",
            description=None,
            org=None,
            region=None,
            domain=None,
            subdomain=None,
            layer=None,
            product=None,
            model=None,
        )
    ],
    outputs=[
        dict(
            kind="TestOutput",
            name="write_something",
            description=None,
            org=None,
            region=None,
            domain=None,
            subdomain=None,
            layer=None,
            product=None,
            model=None,
        )
    ],
)
