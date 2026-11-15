# Docstring Conventions

## Rules

- Follow the [Google docstring format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- Each paragraph must describe a single feature, behavior, constraint, mode, or edge case.
- Document every constructor parameter except `**options`.
- Link the plugin's documentation page in its own paragraph, right before `Attributes:`. For
  Tiozin core plugins, use `https://github.com/fdmorison/tiozin/blob/main/docs/{family}/{purpose}-{role}.md`.
- The YAML example is required: it is the primary way users configure plugins declaratively; use the appropriate role section (`inputs`, `transforms`, `outputs`, `runners`, `registries`).

## Template

```python
"""
<One-sentence summary>

<Paragraph describing a feature, behavior, constraint, mode, or edge case>

<Additional paragraphs as needed, one topic per paragraph>

For the full guide and examples, refer to:

<link to the plugin's documentation page>

Attributes:
    <parameter>:
        <description>

Examples:

    ```python
    <ClassName>(...)
    ```

    ```yaml
    <role>s:
      - kind: <ClassName>
        ...
    ```
"""
```

## Example

```python
"""
Reads files from Acme's platform.

Supports multiple input formats.

Behavior may vary depending on the configured execution mode.

For the full guide and examples, refer to:

https://docs.acme.com/tiozin/acme-file-input

Attributes:
    path:
        Path or list of paths to read from.

    format:
        File format. Defaults to ``"parquet"``.

Examples:

    ```python
    AcmeFileInput(
        path="/data/events",
        format="json",
    )
    ```

    ```yaml
    inputs:
      - kind: AcmeFileInput
        path: /data/events
        format: json
    ```
"""
```
