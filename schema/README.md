# pyems JSON Schema v1.0

This directory contains the formal JSON contract for the `pyems` simulation runner.

## Usage
- The schema is located at `v1.json`.
- All coordinates and dimensions must be in the scale specified by the top-level `simulation.unit` field (default `1e-3` for mm).
- Every JSON envelope must include `"schema_version": 1`.

## Extension Policy
- Additive changes (new optional fields) result in a minor version bump (v1.1, v1.2).
- Breaking changes (renaming fields, changing types, deleting fields) require a major version bump (v2.0).
- Propose changes via an ADR (Architectural Decision Record) in `docs/adr/`.
