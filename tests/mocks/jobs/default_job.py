job = dict(
    kind="LinearJob",
    name="default_job",
    org="tiozin",
    region="latam",
    domain="data",
    subdomain="platform",
    layer="refined",
    product="noop",
    model="noop",
    runner={
        "kind": "NoOpRunner",
    },
    inputs=[
        {
            "kind": "NoOpInput",
            "name": "noop_input",
        }
    ],
    transforms=[
        {
            "kind": "NoOpTransform",
            "name": "noop_transform",
        }
    ],
    outputs=[
        {
            "kind": "NoOpOutput",
            "name": "noop_output",
        }
    ],
)
