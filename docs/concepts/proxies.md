# Tio Proxy: Adding Cross Cutting Family Features

When you build a family (a set of Inputs, Transforms, and Outputs for a specific engine), you often want the same behavior everywhere: logging, debug options, shortcuts to the session. Repeating that code in every step is error-prone. `@tioproxy` is how a provider family adds its own features and behaviors to every Tiozin it ships.

It implements the [Proxy pattern](https://refactoring.guru/design-patterns/proxy): a proxy wraps the real Tiozin and adds behavior around its methods. The framework and the Tiozin do not know the proxy is there. This is different from [middleware or chain-of-responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility), where multiple handlers decide whether to pass a request forward. A proxy wraps a single target. You are extending an object, not building a request pipeline.

## Adding Behavior

The simplest proxy runs code before and after a step method. Here, `SparkLogProxy` logs the start and end of every transform in `SparkFilterTransform`:

```python
import wrapt
from tiozin import tioproxy, Transform
from pyspark.sql import DataFrame


class SparkLogProxy(wrapt.ObjectProxy):
    def transform(self, *data: DataFrame) -> DataFrame:
        self.info("transform started")
        df = self.__wrapped__.transform(*data)
        self.info("transform finished")
        return df


@tioproxy(SparkLogProxy)
class SparkFilterTransform(Transform[DataFrame]):
    def transform(self, *data: DataFrame) -> DataFrame:
        return data[0].filter("status = 'active'")
```

```yaml
transforms:
  - kind: SparkFilterTransform
    name: filtered
# → logs "transform started" and "transform finished" on every run
```

`self.info()` is a structured logging method inherited from the `Loggable` mixin that all Tiozin components extend. `wrapt.ObjectProxy` forwards attribute access to the wrapped object, so calling `self.info()` inside a proxy works the same as calling it on the Tiozin directly.

The proxy is invisible to the step author. It adds behavior automatically.

## Adding a family-level feature

A proxy can also react to configuration the user sets in YAML. That is how you add a feature (like `show: true`) that any step can opt into without changing the step itself.

Every step in Tiozin collects any extra YAML properties that are not declared constructor parameters into `self.options`. When a user sets `show: true`, the value lands in `self.options["show"]`. The proxy reads it and calls `df.show()` after the transform:

```python
import wrapt
from tiozin import tioproxy, Transform
from pyspark.sql import DataFrame


class SparkDebugProxy(wrapt.ObjectProxy):
    def transform(self, *data: DataFrame) -> DataFrame:
        df = self.__wrapped__.transform(*data)
        if self.options.get("show"):
            df.show()
        return df


@tioproxy(SparkDebugProxy)
class SparkFilterTransform(Transform[DataFrame]):
    def transform(self, *data: DataFrame) -> DataFrame:
        return data[0].filter("status = 'active'")
```

```yaml
transforms:
  - kind: SparkFilterTransform
    name: filtered
    show: true    # lands in self.options["show"], triggers df.show() after transform
```

## Explicit Properties with a Mixin

Reading `show` from `options` works, but it is implicit: nothing in the code tells you that `show` exists or what it does. A mixin makes it explicit by declaring `show` as a constructor parameter, keeping it out of `options` and making it visible to IDEs:

```python
import wrapt
from tiozin import tioproxy, Transform
from pyspark.sql import DataFrame


class SparkStepMixin:
    def __init__(self, *args, show: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.show = show


class SparkDebugProxy(wrapt.ObjectProxy):
    def transform(self, *data: DataFrame) -> DataFrame:
        df = self.__wrapped__.transform(*data)
        if self.show:
            df.show()
        return df


@tioproxy(SparkDebugProxy)
class SparkFilterTransform(SparkStepMixin, Transform[DataFrame]):
    def transform(self, *data: DataFrame) -> DataFrame:
        return data[0].filter("status = 'active'")
```

```yaml
transforms:
  - kind: SparkFilterTransform
    name: filtered
    show: true    # passed to SparkStepMixin.__init__ as show=True
```

The proxy reads `self.show` directly instead of going through `options`.

## Sharing behavior and features across a family

Applying `@tioproxy` to every step separately means repeating the decorator. The idiomatic approach is to apply it to shared base classes instead. Every step that extends one of those bases inherits the proxies automatically.

At this stage, the proxies also need to cover `read()` and `write()` so the behavior applies to Inputs and Outputs too, not just Transforms:

```python
import wrapt
from tiozin import tioproxy, Input, Transform, Output
from pyspark.sql import DataFrame


class SparkStepMixin:
    def __init__(self, *args, show: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.show = show


class SparkLogProxy(wrapt.ObjectProxy):

    def read(self) -> DataFrame:
        self.info("read started")
        df = self.__wrapped__.read()
        self.info("read finished")
        return df

    def transform(self, *data: DataFrame) -> DataFrame:
        self.info("transform started")
        df = self.__wrapped__.transform(*data)
        self.info("transform finished")
        return df

    def write(self, data: DataFrame) -> DataFrame:
        self.info("write started")
        df = self.__wrapped__.write(data)
        self.info("write finished")
        return df


class SparkDebugProxy(wrapt.ObjectProxy):

    def read(self) -> DataFrame:
        df = self.__wrapped__.read()
        if self.show:
            df.show()
        return df

    def transform(self, *data: DataFrame) -> DataFrame:
        df = self.__wrapped__.transform(*data)
        if self.show:
            df.show()
        return df

    def write(self, data: DataFrame) -> DataFrame:
        if self.show:
            data.show()
        return self.__wrapped__.write(data)


# The first proxy listed is the outermost wrapper and runs first.
# SparkLogProxy logs before SparkDebugProxy checks show.
@tioproxy(SparkLogProxy, SparkDebugProxy)
class SparkInput(SparkStepMixin, Input[DataFrame]):
    pass

@tioproxy(SparkLogProxy, SparkDebugProxy)
class SparkTransform(SparkStepMixin, Transform[DataFrame]):
    pass

@tioproxy(SparkLogProxy, SparkDebugProxy)
class SparkOutput(SparkStepMixin, Output[DataFrame]):
    pass
```

```yaml
inputs:
  - kind: SparkOrdersInput    # extends SparkInput
    name: orders
    show: true

transforms:
  - kind: SparkFilterTransform    # extends SparkTransform
    name: filtered
    show: true

outputs:
  - kind: SparkFileOutput    # extends SparkOutput
    name: sink
    path: .output/orders
    format: parquet
```

`SparkOrdersInput` extends `SparkInput` and `SparkFilterTransform` extends `SparkTransform`. Both get logging and `show` without any extra code because it is a family-level feature.

## Summary

Here is what the proxy gives you as a family developer:

- Proxy classes must inherit from `wrapt.ObjectProxy`.
- Attach a proxy with `@tioproxy(ProxyClass)`. Combine multiple proxies in one call: `@tioproxy(ProxyA, ProxyB)`. The first proxy listed is the outermost wrapper and runs first.
- Apply `@tioproxy` to base classes (`SparkInput`, `SparkTransform`, `SparkOutput`) to share behavior across the whole family without repeating the decorator on every step.
- Every step collects undeclared YAML properties into `self.options`. Use `self.options.get("key")` to read them in a proxy without changing the step class. Use a mixin constructor to declare the field explicitly and keep it out of `options`.
- Use `self.__wrapped__` inside a proxy to call the original implementation without triggering other proxies.
- Proxies compose across the hierarchy. If `Transform` has a proxy and `SparkTransform` adds another, both apply to any step that extends `SparkTransform`.
