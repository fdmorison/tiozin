# Glossary

## kind
The class name of a Tiozin plugin. Set in YAML to tell Tiozin which plugin class to load and instantiate for a given step.

## Family
A plugin provider. Groups Tiozins that share the same runtime and conventions.

## Tio
A provider package. The concrete installable unit that delivers a Family (e.g. `tio_spark`, `tio_duckdb`).

## Tiozin
A plugin offered by a Tio. The smallest pluggable unit in the framework. Every Job, Runner, Input, Transform, Output, and Registry is a Tiozin.

## Role
The functional category of a Tiozin: Job, Runner, Input, Transform, Output, or Registry.

## Job
A Tiozin that implements a pipeline DAG, composing a Runner, Inputs, Transforms, and Outputs.

## Runner
A Tiozin that implements an execution engine for a Job.

## Input
A Tiozin that implements a data source.

## Transform
A Tiozin that implements data modification logic.

## CoTransform
A Transform variant that receives all current datasets as positional arguments. Requires at least two datasets.

## Output
A Tiozin that implements a data destination.

## Registry
A Tiozin that implements a metadata service available through the execution context.

## Context
The execution scope of a running unit (app, job, or step). Carries everything that unit needs to execute: metadata, registries, runtime state, and utilities. Designed as an API so developers can explore what is available through code completion, without importing individual modules.

## tiozin.yaml
The main application configuration file defining registries, defaults, and plugin settings.

## tioproxy
A decorator that wraps Tiozin instances with proxy behavior.
