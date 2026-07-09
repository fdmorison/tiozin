# Pull Request Writing Guide

This guide explains how to adapt the content of `.github/pull_request_template.md` for each pull request type.

The template defines the document structure and formatting. This guide explains how to fill the template for each pull request type.

The examples use a fictional `tio_acme` family. They show only the content of each section, omitting template-specific formatting such as section headings, Notes metadata, References, and the checklist.

## Rules

- All PRs must follow `.github/pull_request_template.md`.
- When this guide and the template disagree, the template wins.
- Unless otherwise noted, structure **Description** in two paragraphs:
  1. A single, one-line sentence introducing the PR goal.
  2. An optional at most 2 lines paragraph that further develops the introduced goal.
  3. Keep both paragraphs focused on the same idea.
- Whenever practical, include and develop a code or YAML example in **Notes**.

## feat

Description introduces the new capability and expands on the user benefit or resulting behavior.
Usage examples and design rationale belong in **Notes**.

**Title:** `feat(tio_acme): Add Acme transformer`

*Description*

Acme records can now be normalized into flat tables.

Jobs consuming Acme data no longer need custom transformation code to flatten nested records. Each record becomes one output row, and output columns can be renamed to match the target schema.

*What*

- Jobs can normalize nested Acme records into a flat schema.
- Output columns can be renamed through configuration.
- Documentation and tests cover the new capability.

*Notes*

```yaml
transforms:
  - kind: AcmeTransformer
    mappings:
      user.id: user_id
```

## fix

Description is structured in three parts:

1. Describe the observable defect.
2. Show verified evidence of the defect in a code block. The evidence may be defective code, an error message, incorrect output, or reproduction steps that were actually produced.
3. Describe how the issue is resolved without explaining the implementation.

Use only concrete evidence that was actually verified. Do not invent content.

**Title:** `fix(tio_acme): Remove duplicate slash from resource URLs`

*Description*

The code contained broken imports that referenced a module that does not exist.

```python
from .registry import LineageRegistry
from .registry import SchemaRegistry
```

The issue is resolved by updating the imports to reference the modules where the registry classes are actually defined.

*What*

- The imports were fixed
- Lineage and schema proxies now reference the correct registry.

## refactor

Description introduces what was reorganized and then explains the new organization, explicitly stating whether behavior changed.

Focus on the resulting organization rather than the code movement.

**Title:** `refactor(tio_acme): Restructure Acme record parsing`

*Description*

Acme record parsing and column mapping are now separate responsibilities.

The parsing and mapping stages can now evolve independently while preserving the same observable behavior.

*What*

- Record parsing and column mapping are separate processing stages.

## docs

Description introduces what is now documented and then explains what readers can now understand or accomplish.

**Title:** `docs(tio_acme): Document the Acme family`

*Description*

The Acme family is now documented.

Readers can now configure the Acme family and its plugins without reading the source code.

*What*

- Added guide covering connection setup and plugin configuration.
- README index updated to reference the new guide.

## chore

Description introduces the operational improvement and then explains the resulting workflow or maintenance benefit.

**Title:** `chore(tio_acme): Run Acme integration tests in CI`

*Description*

Every pull request now runs the Acme integration tests.

Regressions in the Acme family are detected during code review instead of after merging.

*What*

- A new Github action was added.
- Github workflow were updated to run the integration tests.
- Fixed broken tests.

## perf

Description introduces the performance improvement and then explains where users benefit from it.

Implementation techniques belong in **Notes**.

**Title:** `perf(tio_acme): Constant-time record flattening`

*Description*

The Acme transformer now flattens records in constant time.

Jobs maintain the same processing speed regardless of the number of configured column mappings.

*What*

- Processing time no longer grows with the number of configured mappings.
- Performance tests cover large mapping configurations.

*Notes*

Mappings are resolved into a lookup table once per job instead of once per record.
