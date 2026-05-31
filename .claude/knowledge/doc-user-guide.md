# Doc: User Guide

## Overview

A user guide teaches a developer how to use a feature or complete a task.

It follows a progressive disclosure model: start with the simplest working example, then introduce one new concept at a time. Each section builds on the previous one and adds only the complexity needed for the next use case.

User guides include how-to pages (`# How to [Task]`), quick-start guides (`# Quick Start`), and topic guides (`# [Topic] Guide`).

## Rules

- Title: `# How to [Task]`, `# Quick Start`, or `# [Topic] Guide`.
- User guides must open with an example the reader can copy and run, never with theory.
- Apply the progressive disclosure model:
  - Structure sections from simplest to most advanced topics.
  - Each section introduces at most one new topic.
  - Each section builds on topics introduced earlier.
- Go straight to the example.
  - All sections must include examples.
  - Never open a section with theory or concept definitions.
  - Introduce concepts inline as they appear in the example, or link to an existing conceptual page.
  - Do not duplicate examples. Extend or reference earlier examples when possible.
- Always end with `## Next steps`.
  - Link to the next guide, related guides, or conceptual pages.
- Verify every code example against source code or tests before publishing.
- Link to reference pages or conceptual pages instead of documenting them again.

## Template

```markdown
# How to [Task]

<content + example>

## [Topic]

<content + example>

## [Topic]

<content + example>

## Next steps

- Link to the next guide.
- Link to a related guide.
- Link to a relevant conceptual page.
```
