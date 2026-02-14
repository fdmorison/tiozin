# Tiozin

<p align="center">
  <img
    src="https://raw.githubusercontent.com/fdmorison/tiozin/main/docs/img/tiozin.png"
    lt="Tiozin - Your friendly ETL framework"
  />
</p>

---

ETL shouldn't require 80 files, 50 YAMLs, and a PhD in complexity.

Tiozin brings it back to basics: **Transform. Input. Output.** Nothing more, nothing less.

A lightweight Python framework that makes data jobs declarative, testable, and actually enjoyable to write.

## Quick Start

```bash
pip install tiozin
```

**Define a declarative job**

```yaml
kind: LinearJob
name: example_job
owner: tiozin@tiozin.com
maintainer: tiozin
cost_center: tio_scrooge

org: tiozin
region: latam
domain: marketing
layer: refined
product: users
model: customers

runner:
  kind: NoOpRunner
  streaming: false
  log_level: "{{ ENV.LOG_LEVEL }}"

inputs:
  - kind: NoOpInput
    name: load_it
    layer: raw
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{model}}/date={{ DAY[-1] }}

transforms:
  - kind: NoOpTransform
    name: do_something
    strategy: sha256

outputs:
  - kind: NoOpOutput
    name: save_it
    path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{model}}/{{ today }}
```

Run it:

```bash
$ tiozin run examples/jobs/dummy.yaml
```

**Using Python directly**

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("examples/jobs/dummy.yaml")
```
Done. No ceremony, no boilerplate.

## Philosophy

Your uncle's advice: Keep it simple, readable, and testable.

- **Declarative** – Define what, not how
- **Pluggable** – Swap runners, registries, plugins as needed
- **Metadata** – Built-in metadata integration
- **Observable** – Logs that help
- **Testable** – Mock anything, validate everything

No magic. No surprises. Just clean data pipelines.

## Who is Tiozin for?
Tiozin is human-readable and machine-generatable:

- Data engineers who want reusable pipeline components
- Teams that value declarative jobs
- Projects that require testable ETL logic
- Pipelines where metadata is connected to the execution model
- Teams leveraging AI agents 🤖 to author and maintain data jobs

## Documentation

- [Tiozin Family: Understanding Tios and Tiozins](docs/family.md)
- [Working with Jobs](docs/jobs.md)
- [Inputs, Transforms & Outputs](docs/transforms.md)
- [Runners](docs/runners.md)
- [Registries](docs/registries.md)
- [Examples](docs/examples.md)
- [API Reference](docs/api.md)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## License

This project is licensed under the [Mozilla Public License 2.0](LICENSE).
