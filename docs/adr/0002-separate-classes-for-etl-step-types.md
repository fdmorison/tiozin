# ADR 0002: Separate Classes for Input, Transform, and Output

## Status

Accepted

## Context

Tiozin's ETL layer is structured around three step types — `Input`, `Transform`, and `Output` —
each with a corresponding proxy (`InputProxy`, `TransformProxy`, `OutputProxy`) and manifest
(`InputManifest`, `TransformManifest`, `OutputManifest`).

The three step types share structural similarities: lifecycle hooks (`setup`, `teardown`), schema
handling, lineage tracking, dataset registration, timing, and logging. A natural reaction when
reading this code for the first time is to flag the duplication and propose a shared base class
or mixin.

A design decision was required to define:

* Whether the three step types should share a common implementation base
* Whether the three proxy and manifest types should be collapsed or extracted
* How to preserve intentional behavioral differences without them being mistaken for bugs
* How to keep the door open for future unification without forcing it prematurely

---

## Decision

`Input`, `Transform`, and `Output` are defined as **separate, independent classes** with no
shared implementation base beyond `Tiozin` (the framework root).

`InputProxy`, `TransformProxy`, and `OutputProxy` are likewise **separate, independent classes**
with no shared proxy base.

`InputManifest`, `TransformManifest`, and `OutputManifest` follow the same principle — each is
a separate, independent class with no shared manifest base beyond `Manifest`.

Behavioral similarities are maintained **by convention and discipline**, not by inheritance.

---

## Behavioral Differences That Motivate Separation

The three step types are not variations of a single concept. They have distinct contracts:

| Concern | Input | Transform | Output |
|---|---|---|---|
| Execution method | `read()` | `transform(*data)` | `write(*data)` |
| Accepts data arguments | No | Yes | Yes |
| Returns | `Dataset` | `Dataset` | raw data (unwrapped) |
| Accepts static outputs | Yes | No | Yes |
| Unwraps input datasets | No | Yes | Yes |

These differences are intentional and reflect the distinct role each type plays in the pipeline.
Collapsing them into a shared base would require conditional branching that obscures those roles.

---

## Rationale

* **Premature unification is more costly than duplication**: merging classes before their
  contracts stabilize forces artificial generalization and makes individual evolution harder.
* **Independent evolution**: each step type is expected to accumulate behavior specific to its
  role as the framework matures. Inputs may gain schema validation on read; Outputs may gain
  write confirmation or rollback; Transforms may gain intermediate schema assertion. Shared
  inheritance would make this additive work harder.
* **Differences are semantic**: the similarities between the three are implementation accidents,
  not design intent. The meaningful unit is the contract of each type, not the code they share.
* **Observation before abstraction**: the right moment to extract a base class or mixin is when
  the three types have stabilized and their common ground is well-understood. That moment has
  not yet arrived.

---

## Conventions Maintained to Facilitate Future Unification

To prevent the classes from diverging by accident rather than intent, the following conventions
are enforced:

* **Proxy structure**: all three proxies follow the same internal structure — `setup` and
  `teardown` raise `AccessViolationError`, the execution method runs inside `context` and
  `TiozinTemplateOverlay`, and lifecycle timestamps are recorded in the same order.
* **Schema handling pattern**: all three guard on `schema_subject` before calling the registry,
  and assign to `context.output_schema` in the same position.
* **Manifest structure**: all three manifests declare the same field groups — identity, business
  taxonomy, and specific fields — in the same order.

These conventions make accidental divergence visible in code review and make eventual extraction
mechanical rather than investigative.

---

## Consequences

### Positive

* Each step type can evolve independently without affecting the others
* Behavioral differences are explicit and readable in each class
* No risk of a base class change producing unexpected side effects across all three types
* Future unification, if warranted, is straightforward because conventions are already aligned

### Negative

* Contributors unfamiliar with this decision will likely flag the duplication as a defect
* Discipline is required to keep the three classes aligned where alignment is intentional
* Any cross-cutting change must be applied in three places

These trade-offs are intentional and accepted.

---

## Alternatives Considered

### Shared base class or mixin

Rejected because the three types have meaningfully different contracts. A shared base would
either be too abstract to be useful or would require conditional logic that obscures the
purpose of each type.

### Single generic `StepProxy` with type parameters

Rejected for the same reason. The differences between `read()`, `transform()`, and `write()`
are not variations of a single operation — they are distinct contracts with different
signatures, argument handling, and return semantics.

---

## Notes

When a behavioral pattern appears in all three classes with no variation whatsoever, that is a
signal to consider extraction. When a pattern appears in all three but with meaningful
differences in each, that is a signal to leave it in place and document the intent.

This ADR should be revisited once `Input`, `Transform`, and `Output` have stabilized and at
least one full release cycle of independent evolution has been observed.
