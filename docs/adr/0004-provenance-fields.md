# ADR 0004: Provenance Fields

## Status
Accepted

## Context
When a simulation fails or a mesh warning is issued, it is difficult to trace the offending JSON entry back to the original CAD object in FreeCAD.

## Decision
- Objects in the JSON envelope (`primitives`, `ports`, `lumped_elements`, `materials`) will support an optional `source_label` string field.
- The `pyems` runner will ignore this field during simulation but MUST surface it in error messages, logs, and events.
- The FreeCAD workbench will populate this with the `Label` of the originating document object.

## Consequences
- Significantly improves the debugging experience for end users.
- Connects the headless runner logs back to the interactive CAD environment.

### What would force a v2?
Making `source_label` mandatory or renaming it to something else (e.g., `cad_id`).
