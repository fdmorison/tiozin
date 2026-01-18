# Tiozin

<p align="center">
  <img src="docs/tiozin.png" alt="Tiozin - Your friendly ETL framework">
</p>

---

ETL shouldn't require 80 files, 50 YAMLs, and a PhD in complexity.

Tiozin brings it back to basics: **Transform. Input. Output.** Nothing more, nothing less.

A lightweight Python framework that makes data jobs declarative, testable, and actually enjoyable to write.

## Quick Start

```bash
pip install tiozin
```

**Option 1: Define a job in YAML**

```yaml
kind: Job
name: kinglear_word_count_job

org: tiozin
region: latam
domain: literature
product: shakespeare
model: kinglear
layer: refined

runner:
  kind: SparkRunner

inputs:
  - kind: SparkFileInput
    name: load_poems
    path: s3://{{org}}-{{domain}}-raw/{{product}}/{{model}}/date={{ DAY[-1] }}

transforms:
  - kind: SparkWordCountTransform
    name: word_count

outputs:
  - kind: SparkFileOutput
    name: save_word_counts
    path: s3://{{org}}-{{domain}}-{{layer}}/{{product}}/{{model}}/date={{ today }}
```

Run it:

```bash
tiozin run examples/jobs/shakespeare/kinglear_word_count_job.yaml
```

**Option 2: Use Python directly**

```python
from tiozin import TiozinApp

app = TiozinApp()
app.run("examples/jobs/shakespeare/kinglear_word_count_job.yaml")
```

Done. No ceremony, no boilerplate.

## Documentation

- [Installation](docs/installation.md)
- [Jobs](docs/pipeline.md)
- [Runners](docs/runners.md)
- [Transforms, Inputs & Outputs](docs/transforms.md)
- [Registries](docs/registries.md)
- [Plugins](docs/plugins.md)
- [Testing](docs/testing.md)

## Philosophy

Your uncle's advice: Keep it simple, readable, and testable.

- **Declarative** – Define what, not how
- **Pluggable** – Swap runners, registries, plugins as needed
- **Metadata** – Built-in metadata integration
- **Observable** – Logs that help
- **Testable** – Mock anything, validate everything

No magic. No surprises. Just clean data pipelines.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## License

This project is licensed under the [Mozilla Public License 2.0](LICENSE).
