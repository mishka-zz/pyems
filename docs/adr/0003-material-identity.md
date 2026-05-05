# ADR 0003: Material Identity

## Status
Accepted

## Context
Materials need to be reusable across multiple geometric primitives. We need a robust way to link primitives to material definitions.

## Decision
- Each material in the `materials` array MUST have a unique `name` (string).
- Geometric `primitives` and `lumped_elements` will reference materials using this name (Foreign Key).
- Duplicate material names are considered a validation error.

## Consequences
- Supports the "Library + Binding" pattern in the FreeCAD workbench.
- Simplifies JSON generation by avoiding nested redundant material definitions.
- Validation requires a two-pass approach or a lookup table to ensure all FKs resolve.

### What would force a v2?
Removing the `name` requirement or changing material referencing to use integer IDs instead of strings.
