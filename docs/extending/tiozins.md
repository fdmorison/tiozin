# Creating Pluggable Tiozins

Every component you write for Tiozin is a Tiozin: an Input, a Transform, an Output, a Runner, or a Registry. Each one is discovered by class name and wired into jobs through the same plugin system.

## How Tiozin finds your plugins

Plugin discovery uses Python's `entry_points` mechanism. See [Creating a Provider Family](families.md) for the full registration walkthrough.

Once your package is installed, Tiozin makes your Tiozins available by class name. Users reference them using the `kind` field in any job YAML or Python definition. The framework resolves the class at runtime without any manual wiring.

## Using @tioproxy

Proxies let you add shared methods to every step in your family without repeating code in each class.

See [Tio Proxy](proxies.md) for how the proxy chain is built across the class hierarchy.

## Implementing ETL Tiozins

Runners, Inputs, Transforms, and Outputs are the building blocks of a data pipeline. [Implementing ETL Tiozins](runtime.md) walks you through each one with a complete SQLite example, ending with a runnable job.

- [Implementing a Runner](runtime.md#implementing-a-runner)
- [Implementing an Input](runtime.md#implementing-an-input)
- [Implementing a Transform](runtime.md#implementing-a-transform)
- [Implementing an Output](runtime.md#implementing-an-output)
- [Putting it all together](runtime.md#putting-it-all-together)

Once you have the basics working, these sections cover common patterns and constraints you will run into:

- [Lineage](lineage.md)
- [Stateless steps, stateful runner](runtime.md#stateless-steps-stateful-runner)
- [Eager and lazy execution](runtime.md#eager-and-lazy-execution)

## Implementing Registry Tiozins

Registries are metadata services: secrets, settings, schemas, lineage, metrics. [Working with Registries](registry.md) covers how to implement a custom registry and how to access registries from inside your plugins.

- [Implementing a Registry](registry.md#implementing-a-registry)
- [Accessing Registries from Plugins](registry.md#accessing-registries-from-plugins)
