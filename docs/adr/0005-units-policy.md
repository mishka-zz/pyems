# ADR 0005: Units Policy

## Status
Accepted

## Context
FreeCAD uses millimeters internally, while openEMS and `pyems` support arbitrary scale factors. Mixing units often leads to floating-point precision issues in the Yee-grid mesher.

## Decision
- The JSON envelope will support a `unit` property (positive float).
- The FreeCAD workbench bridge MUST always write `unit: 1e-3` (mm).
- All coordinates in the JSON MUST be in the units specified by `unit`.

## Consequences
- Ensures consistency between the CAD model and the solver.
- Stabilizes `pyems` meshing logic by providing a predictable coordinate scale.
- Simplifies the translation bridge (no per-object unit conversion needed).

### What would force a v2?
Changing the `unit` field to a string (e.g., `"mm"`) or removing global unit scaling in favor of per-object units.
