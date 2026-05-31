# Creating Pluggable Tiozins

Every component written for Tiozin is a Tiozin: an Input, a Transform, an Output, a Runner, or a Registry. Each one is discovered by class name and wired into jobs through the same plugin system.

## How Tiozin Finds Plugins

Plugin discovery uses Python's `entry_points` mechanism. See [Creating a Provider Family](families.md) for the full registration walkthrough.

Once the package is installed, Tiozin makes its Tiozins available by class name. Users reference them using the `kind` field in any job YAML or Python definition. The framework resolves the class at runtime without any manual wiring.

## Using @tioproxy

Proxies add shared methods to every step in a family without repeating code in each class.

See [Tio Proxy](proxies.md) for how the proxy chain is built across the class hierarchy.

## Implementing ETL Tiozins

Runners, Inputs, Transforms, and Outputs are the building blocks of a data pipeline. [Implementing ETL Tiozins](runtime.md) walks through each one with a complete SQLite example, ending with a runnable job.

- [Implementing a Runner](runtime.md#implementing-a-runner)
- [Implementing an Input](runtime.md#implementing-an-input)
- [Implementing a Transform](runtime.md#implementing-a-transform)
- [Implementing an Output](runtime.md#implementing-an-output)
- [Putting it all together](runtime.md#putting-it-all-together)

Once the basics are working, these sections cover common patterns and constraints to consider:

- [Lineage](lineage.md)
- [Stateless steps, stateful runner](runtime.md#stateless-steps-stateful-runner)
- [Eager and lazy execution](runtime.md#eager-and-lazy-execution)

## Implementing Registry Tiozins

Registries are metadata services: secrets, settings, schemas, lineage, metrics. [Working with Registries](registry.md) covers how to implement a custom registry and how to access registries from inside plugins.

- [Implementing a Registry](registry.md#implementing-a-registry)
- [Accessing Registries from Plugins](registry.md#accessing-registries-from-plugins)
