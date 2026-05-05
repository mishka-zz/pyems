# ADR 0001: Schema Versioning

## Status
Accepted

## Context
The `freecad-ems` workbench and the `pyems` engine evolve at different rates. We need a way to ensure compatibility and allow for breaking changes in the JSON contract without silent failures.

## Decision
- The JSON envelope MUST include a top-level `schema_version` field.
- The `schema_version` MUST be an integer (starting at `1`).
- The `pyems` runner MUST validate this version and refuse to execute if the major version is unknown or unsupported.

## Consequences
- The workbench and engine can be updated independently.
- Reproducible bug reports can be tied to specific schema versions.
- Future breaking changes (v2.0) will require an explicit upgrade path or a multi-version runner.

### What would force a v2?
Renaming top-level keys or changing the `schema_version` type from integer to string.
