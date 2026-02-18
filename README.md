# Tiozin

<p align="center">
  <img
    src="https://raw.githubusercontent.com/fdmorison/tiozin/main/docs/img/tiozin.png"
    alt="Tiozin - Your friendly ETL framework"
  />
</p>

---

ETL shouldn't require 80 files, 50 YAMLs, and a PhD in complexity.

Tiozin brings it back to basics: **Transform. Input. Output.** Nothing more, nothing less.

A lightweight Python framework that makes data jobs declarative, testable, and actually enjoyable to write.

## Philosophy

Your uncle's advice: keep it simple, readable, and testable.

Tiozin is built around a small set of principles that are not features but constraints that shape the design.

- **Declarative** — Define what, not how
- **Pluggable** — Swap runners, registries, and plugins when needed
- **Metadata-native** — Execution and metadata walk together
- **Observable** — Logs that actually help
- **Testable** — Mock anything, validate everything

## One-Minute Example

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
subdomain: campaigns
layer: refined
product: users
model: customers

runner:
  kind: NoOpRunner
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

## Who is Tiozin for?
Tiozin is human-readable and machine-generatable:

- Data engineers who want reusable pipeline components
- Teams that value declarative jobs
- Projects that require testable ETL logic
- Pipelines where metadata is connected to the execution model
- Teams leveraging AI agents 🤖 to author and maintain data jobs

## Documentation

### Getting Started
- [Your First Job](https://github.com/fdmorison/tiozin/blob/main/docs/quickstart.md)

### Concepts
- [Family Model: Tios and Tiozins](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/family.md)
- [Jobs](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/jobs.md)
- [Runners](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/runners.md)
- [Inputs, Transforms & Outputs](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/steps.md)
- [Registries](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/registries.md)
- [Tio Proxy](https://github.com/fdmorison/tiozin/blob/main/docs/concepts/proxies.md)

### Extending Tiozin
- [Creating a Provider Family](https://github.com/fdmorison/tiozin/blob/main/docs/extending/families.md)
- [Creating Pluggable Tiozins](https://github.com/fdmorison/tiozin/blob/main/docs/extending/tiozins.md)

### Reference
- [Examples](https://github.com/fdmorison/tiozin/blob/main/docs/examples.md)
- [API Reference](https://github.com/fdmorison/tiozin/blob/main/docs/api.md)
- [Settings](https://github.com/fdmorison/tiozin/blob/main/docs/settings.md)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](https://github.com/fdmorison/tiozin/blob/main/docs/CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the [Mozilla Public License 2.0](LICENSE).
