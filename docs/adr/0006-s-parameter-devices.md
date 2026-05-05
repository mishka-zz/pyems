# ADR 0006: S-Parameter Devices

## Status
Accepted

## Context
Users frequently want to include S-parameter defined components (Touchstone files) in their simulations.

## Decision
- The v1.0 schema will NOT include a top-level `s_param_devices` key.
- S-parameter devices will be handled workbench-side using two strategies:
    1. **RLC Synthesis**: Fitting a lumped equivalent circuit (narrowband).
    2. **Port-Pair Post-processing**: Placing two ports and cascading S-matrices after the FDTD run.
- Both strategies map to existing schema features (`lumped_elements` or `ports`).

## Consequences
- Keeps the JSON contract focused on features supported natively by the FDTD solver.
- Avoids premature commitment to a feature that requires significant engine-side research.

### What would force a v2?
Adding a native `s_param_devices` top-level key to the schema.
