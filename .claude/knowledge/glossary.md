# Glossary

## Family
A named collection of Tiozin plugins targeting a provider or execution technology.

## Tiozin
A plugin class inheriting from `Tiozin`. Each Tiozin belongs to one Family and one Role.

## Role
The functional category of a Tiozin: Job, Runner, Input, Transform, Output, or Registry.

## Job
A data job definition composed of a Runner, Inputs, Transforms, and Outputs.

## Runner
The execution engine for a Job.

## Input
A stateless data source plugin.

## Transform
A stateless data transformation plugin.

## CoTransform
A Transform variant accepting multiple named inputs.

## Output
A stateless data sink plugin.

## Registry
A metadata service available through the execution context.

## Context
A singleton runtime context scoped to a single job execution.

## tiozin.yaml
The main application configuration file defining registries, defaults, and plugin settings.

## tioproxy
A decorator that wraps Tiozin instances with proxy behavior.
