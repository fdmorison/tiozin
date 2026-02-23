# Tio Proxy

A Tio Proxy wraps Tiozin instances to inject cross-cutting behavior — things like context activation, logging, and session injection — without touching the business logic inside each step.

---

## How it works

When you instantiate any Tiozin (a job, runner, input, transform, or output), the framework automatically wraps it in one or more proxy objects. The wrapping happens transparently at construction time. You get back a proxy, but it behaves exactly like the original object.

The `@tioproxy` decorator registers which proxies a class should use. When the class is instantiated, `TioProxyMeta` builds the proxy chain in the right order.

---

## Built-in proxies

The framework ships three built-in proxies that run automatically:

| Proxy | Applied to | What it adds |
|---|---|---|
| `JobProxy` | Job | Context activation, runner lifecycle management, step orchestration |
| `RunnerProxy` | Runner | Context injection |
| `StepProxy` | Input, Transform, Output | Context activation, logging, engine session injection |

You don't configure these. They're always active.

---

## Proxy inheritance

Proxies compose across the class hierarchy. Parent proxies wrap first; child proxies wrap afterward.

```python
# From the framework source:
@tioproxy(JobProxy)
class Job(Tiozin):
    ...

@tioproxy(SparkProxy)
class SparkInput(Input):
    ...

# SparkInput() → JobProxy(StepProxy(SparkProxy(instance)))
```

Each class in the hierarchy can add its own proxies. The final chain wraps from outermost (parent) to innermost (most-derived child).

---

## Using @tioproxy in a custom family

When building a provider family, use `@tioproxy` to inject family-specific behavior into your base classes — for example, to expose the native session as a shorthand property on every step:

```python
from tiozin import tioproxy, Input
import wrapt

class SparkStepProxy(wrapt.ObjectProxy):
    @property
    def spark(self):
        return self.context.runner.session

@tioproxy(SparkStepProxy)
class SparkInput(Input):
    def read(self):
        return self.spark.read.parquet(self.path)
```

A class may only use `@tioproxy` once. To register multiple proxies, pass them all in a single call:

```python
@tioproxy(ProxyA, ProxyB)
class MyInput(Input):
    ...
```

Proxy classes must inherit from `wrapt.ObjectProxy`.

See [Creating Pluggable Tiozins](../extending/tiozins.md) for complete examples.
