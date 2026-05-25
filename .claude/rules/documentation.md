# Documentation Rules

## Audience

Write for any developer using the framework. Introduce Tiozin terms before using them. Users are capable adults — clarity, not condescension.

---

## Tone

- Use active voice
- Develop one idea per sentence or paragraph.
- Write prose that reads naturally to a human, not a chain of robotic clauses.
- No filler: "It is worth noting that", "In order to", "In this section, we will"
- No marketing: "powerful", "seamless", "robust", "intuitive"
- No academic framing: "This document describes", "The following section covers"
- No em-dashes or en-dashes. Use a period, colon, or parentheses instead
- Headings are conversational, not bureaucratic:


```
# ❌ "The TemplateDate class provides a fluent interface."
# ✔  "The TemplateDate class provides a fluent interface: every property returns a TemplateDate, so you can chain them freely."

# ❌ "Explicit arguments always override defaults. The merge is deep: for nested mappings,
#      only missing or null fields are filled in. Non-null values in the job definition are never replaced."
# ✔  "Job arguments always win. Defaults fill in missing or null fields only, including inside nested mappings."

# ❌ "Introduction", "Overview", "API Surface"
# ✔  "The basics", "Common patterns", "All available options"
```

---

## Structure by document type

### User guides and tutorials

1. One-line purpose statement
2. Simplest possible example
3. Examples in increasing complexity
4. Reference table (when applicable)

Each section builds on the previous — do not redefine earlier code, reference it by name. Explain framework-provided attributes (`self.options`, `self.context`) the first time they appear.

### Conceptual overviews

1. One-line statement of what the concept is and why it exists
2. Explanation with enough context to understand it
3. At least one concrete example
4. Links to related guides or reference pages

### Reference pages

For plugins (Input, Transform, Output, Runner):

1. One-line description
2. Minimal YAML example
3. Single unified properties table (never split by category)
4. One section per parameter that needs explanation, opening with its motivation

For other reference content, structure follows the property set. See Reference Tables below.

### FAQ

**Q: [Question as the user would ask it]**

A: [Direct answer. Code example if needed.]

Group related questions under a heading. Never answer "it depends" without specifying the conditions.

### Troubleshooting

**Symptom:** [What the user observes]

**Cause:** [Why it happens]

**Fix:** [What to do, with code or command when relevant]

Only include entries verifiable against code or tests.

---

## Example standards

- Minimal: no unnecessary fields
- Realistic: drawn from `examples/jobs/`
- Correct: verified against source or tests
- Ordered: simplest to most complex

Every example shows output:

```yaml
# ✔ Correct
path: .output/lake/date={{ D[-1] }}
# → .output/lake/date=2026-01-16

# ❌ Incorrect — no output shown
path: .output/lake/date={{ D[-1] }}
```

---

## Reference tables

Column order: `Property / Syntax | Description | Example output`

- Description: one clause, no period
- Example output: literal rendered value, not a format string
- Group by category with a heading above each table
- List aliases together, not separately
- List all accepted enum values in the property section — never link to external docs as a substitute

---

## File conventions

- Location: `docs/<topic>.md`
- Filename: lowercase, hyphen-separated
- First heading: `# Title Case`
- Section headings: `## Title Case`
- No `---` as horizontal rule
- Python signatures include type hints. Use concrete types; use `Any` only for genuinely generic examples

---

## README index

The README links to documentation. It is not the place for long-form content.

Add new docs under the correct section:

1. Getting Started — tutorials and onboarding
2. Concepts — conceptual explanations
3. Extending Tiozin — extension and integration guides
4. Reference — API tables, property references, feature guides

Never link to files that do not exist.

---

## Verification checklist

- [ ] All behavior verified against source code or tests
- [ ] Every example manually traced
- [ ] No assumed defaults or inferred behavior
- [ ] README index updated if a new file was created
- [ ] Self-review: no contradictions, no stale enumerations, no broken code
