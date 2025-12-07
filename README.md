# Welcome to Tio

<p align="center">
  <img src="docs/tio.png">
</p>

Welcome to Tio, your companion for data orchestration with simplicity, reliability, and elegance.

In a world where data moves faster than structures can keep up, jobs have grown into untamed monsters: massive tools, heavy configurations, and entire ecosystems to master before running a single line. Tio was born to change this. It brings simplicity, clarity, and testable code back to the heart of data flows.

Jobs should be human-sized. They don’t need 80 files, 50 YAMLs, 12 frameworks, or a PhD in complexity. Tio lets you define jobs as if you were having a conversation: direct, clear, expressive.

Transform. Input. Output. Nothing more. Nothing less.

## What is Tio

Tio is a minimalist ETL/ELT framework that combines Data Engineering and Software Engineering to build professional, maintainable data jobs.

It aims to create jobs that are declarative, testable, documentable, and fully pluggable across different data engines such as Spark, SQL warehouses, Apache Beans, and more.

## Documentation Index

For more details, please refer to the documentation:

- [Installation Guide](docs/installation.md) – How to install and get started with Tio
- [Core Concepts](docs/core_concepts.md) – Overview of jobs, steps, runtimes, and metadata
- [Transforms](docs/transforms.md) – Creating and executing transformation steps
- [Inputs](docs/inputs.md) – Connecting to data sources
- [Outputs](docs/outputs.md) – Writing results to data destinations
- [Runners](docs/runners.md) – Executing into different data transformation engines.
- [Job Definition](docs/pipeline.md) – How to define and configure ETL jobs
- [Registry System](docs/registries.md) – Registries, NoOp implementations, and SecretRegistry
- [Family Providers & Plugins](docs/plugins.md) – Built-in and custom provider integrations
- [Lifecycle & Shutdown](docs/lifecycle.md) – Bootstrap and graceful shutdown
- [Testing](docs/testing.md) – Testing strategies, mocks, and best practices

## Tio Manifesto

**The philosophy behind Tio, in six principles:**

- **Jobs should be human-sized**
  Keep them simple, direct, and readable. Avoid unnecessary complexity and boilerplate.

- **Transform, Input, Output**
  Focus on what matters. Every job is composed of clear, purposeful steps.

- **Declarative yet flexible**
  Configure jobs without losing control, clarity, or readability.

- **Extensible and modular**
  Registries, runtimes, and steps can be replaced, extended, or customized as needed.

- **Transparent and observable**
  Logging is useful, not spammy or absent. Metadata registries provide governance, traceability, and lineage. System initialization and shutdown are graceful and observable.

- **Testable by design**
  Every component can be isolated, mocked, and validated with confidence.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
