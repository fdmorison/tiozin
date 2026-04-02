class TemplateString(str):
    """
    Marker for Jinja templates stored as configuration that must be rendered
    at runtime, not during plugin setup.

    Behaves exactly like `str` everywhere in the codebase. The
    `TiozinTemplateOverlay` skips attributes holding a `TemplateString`
    during its scan, preventing premature rendering when context variables
    such as `org` or `domain` are not yet available.
    """
