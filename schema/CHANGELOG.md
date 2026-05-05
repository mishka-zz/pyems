# pyems JSON Schema Changelog

## v1.0 (2026-05-04)
- Initial release of the versioned JSON contract.
- **Breaking Change**: `lumped_elements` moved from `materials` to top-level key.
- **Breaking Change**: `boundary_conditions` is now a 6-element array of structured objects.
- Added `schema_version` (integer, const 1).
- Added `source_label` to all major objects for workbench provenance.
- Added `excitations` list for multi-port support.
- Reserved keys for `nf2ff`, `field_dumps`, `probes`, `pcb_stackup`.
