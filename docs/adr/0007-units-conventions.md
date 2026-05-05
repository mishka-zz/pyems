# ADR 0007: Units Conventions

## Status
Proposed

## Context
A recurring class of bugs in `pyems` involves the confusion between simulation units (e.g., mm, defined by `simulation.unit`) and absolute SI units (e.g., meters, S/m, Hz) required by the underlying `openEMS` C++ engine. 

While coordinates in `CSXCAD` are scaled by the `DeltaUnit` (grid unit), certain material properties like `thickness` and `conductivity` are expected in absolute SI units. Failing to convert between these conventions leads to physically incorrect simulations that may still appear to run correctly (e.g., incorrect loss predictions due to 1000x thickness errors).

## Decision
We establish a strict "Boundary Conversion" architecture to eliminate implicit convention defects.

### 1. The Single Boundary Rule
All conversions from simulation units (SU) to absolute SI units (specifically Meters) MUST occur exclusively within `pyems/csxcad.py`. No other module (ports, runner, simulation) is permitted to perform unit math.

### 2. Convention Map

| Parameter | Unit Convention | Layer: Workbench/JSON | Layer: `pyems` Logic | Layer: `csxcad` Boundary | Layer: Engine (SI) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Coordinates | SU | SU (mm) | SU (mm) | SU (mm) | SU (mm) [1] |
| Dimensions | SU | SU (mm) | SU (mm) | SU (mm) | SU (mm) [1] |
| Thickness | SU | SU (mm) | SU (mm) | **CONVERT (SU -> m)** | m |
| Frequency | SI | Hz | Hz | Hz | Hz |
| Conductivity | SI | S/m | S/m | S/m | S/m |
| Impedance | SI | Ohm | Ohm | Ohm | Ohm |

[1] Engine scales coordinates internally by `GetDeltaUnit()`.

### 3. Naming Convention (Internal)
For ambiguous parameters within `pyems/csxcad.py`, we use the following suffixes:
- `_su`: Simulation units (e.g., `thickness_su`).
- `_m`: Absolute meters.

## Consequences
- **Robustness**: Future additions to the codebase will automatically follow the correct scaling if they use the `csxcad.py` wrappers.
- **Verification**: We can now implement lint-style tests to detect stray unit math outside the boundary.
- **Clarity**: Docstrings must be updated to reflect this contract, and the workbench team can rely on the Glossary in this ADR.
- **Backward Compatibility**: Any user who previously bypassed the API to provide absolute meters for `thickness` will now be broken and must migrate to simulation units.
