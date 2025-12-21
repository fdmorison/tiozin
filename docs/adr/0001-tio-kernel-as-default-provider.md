# ADR 0001: TioKernel as the Default Provider

## Status
Accepted

## Context

Tiozin uses a provider-based plugin system, where each provider ("Tio") supplies a set of plugin implementations such as registries, inputs, transforms, outputs, and runners.

A design decision was required to define:

- How Tiozin boots with minimal or no configuration
- Which provider is always present and provides baseline implementations
- What responsibilities belong to the default provider
- How extensibility and override work without coupling domain logic to the system core
- How to prevent architectural drift while maintaining system completeness

Without a clear boundary, there is a risk of gradually accumulating execution logic, engine-specific behavior, or domain features in the default provider, leading to architectural drift.

---

## Decision

Tiozin defines a single default provider named **TioKernel**.

TioKernel is always present and cannot be disabled or replaced.

TioKernel provides a default implementation for **every supported plugin type**.

While TioKernel itself is fixed, the plugins it supplies act as **defaults** and may be overridden by plugins from other providers, according to provider precedence rules.

The role of TioKernel is to guarantee that the system is always **complete and executable**, even in the absence of additional providers.

---

## Responsibilities of TioKernel

The responsibilities of TioKernel are intentionally limited to providing **safe, predictable, and well-defined defaults**.

Defaults differ in behavior depending on the nature of the concern, but all plugin types are always present.

### Functional defaults

Feature-complete, production-usable implementations for common and stable configuration patterns:

- File-based Job Registry
- Environment-based Secret Registry (including `.env` support)
- File-based Schema Registry
- File-based Settings Registry

These defaults represent opinionated but broadly applicable practices commonly adopted by data teams, such as managing configuration, schemas, and job definitions in files or environment variables.

---

### No-op defaults

Explicit no-op implementations that allow the system to remain complete while making optional or non-executable behavior explicit and safe.

**Optional registries** — concerns that are cross-cutting or not always required:

- Metric Registry
- Lineage Registry
- Audit or Telemetry Registry

These registries may remain as no-op in production when observability or governance concerns are not needed.

**Execution plugins** — allow bootstrapping and validation without real execution:

- Inputs
- Transforms
- Outputs
- Runners

These implementations enable Tiozin to boot, validate configurations, run dry-runs, and demonstrate behavior without performing real execution. They are not intended for production workloads.

---

## Rationale

This decision is based on the following principles:

- **Complete by default**: Every plugin type has a default implementation, ensuring Tiozin can always boot and execute with zero or minimal configuration.

- **Minimal in scope, not in capability**: TioKernel contains only essential system components, but those components may be fully featured when they represent common and stable patterns.

- **Behavioral clarity**: Defaults make system behavior explicit — functionality is either provided, intentionally absent (no-op), or simplified for demonstration, but never implicit or missing.

- **Clear separation of concerns**: TioKernel defines structure and safe defaults; specialized providers define real execution behavior and domain-specific logic.

- **Explicit extensibility**: All defaults are replaceable, preventing tight coupling between the system core and any particular engine or domain.

The name **TioKernel** reflects its foundational role: it guarantees system completeness without imposing execution strategy.

---

## Consequences

### Positive

- Tiozin can boot, validate, and execute with zero or minimal configuration
- The system is always complete; no plugin type is ever missing
- Architectural boundaries are clear and enforceable
- Defaults are explicit, predictable, and easy to reason about
- Providers remain cohesive and purpose-driven

### Negative

- Real production workloads require explicit providers beyond TioKernel
- No-op execution defaults must clearly signal non-production intent
- Slightly higher conceptual overhead for new contributors

These trade-offs are intentional and accepted.

---

## Alternatives Considered

### Partial defaults (only essential plugins)

Rejected because missing default implementations would cause the system to fail during boot.

Without defaults for all plugin types, Tiozin would require explicit configuration or providers
for every concern, making a simple or zero-configuration startup impossible and breaking the
quick-start experience.

### Including real execution logic in the default provider

Rejected to avoid coupling engine-specific or domain-specific behavior to the system core.

### No default provider

Rejected because the system would not be able to boot at all without explicit providers.

Without a default provider, Tiozin would fail during initialization, preventing validation,
demonstration, or any form of simple execution, and making a quick start impossible.

---

## Notes

Any plugin added to TioKernel must justify why a default is necessary for system completeness.

If a plugin can reasonably live in a specialized provider without affecting bootstrapping,
validation, or demonstrability, it does not belong in TioKernel.
