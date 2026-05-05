# ADR 0002: Boundary Encoding

## Status
Accepted

## Context
openEMS expects boundary conditions for all six faces of the simulation volume. The existing implementation often assumes symmetric or global boundaries, which limits antenna and complex PCB simulations.

## Decision
- Boundary conditions will be encoded as a 6-element array corresponding to `[Xmin, Xmax, Ymin, Ymax, Zmin, Zmax]`.
- Each element will be a structured object: `{"type": "PML", "cells": 8}` or `{"type": "PEC"}`.
- PML types MUST include a `cells` count (default 8).

## Consequences
- Allows asymmetric boundary setups (e.g., antenna on a finite ground plane).
- The workbench UI must expose these six independent controls, though it may provide a "Symmetric" macro to fill them.
- `pyems.boundary` logic must be updated to parse this structured format.

### What would force a v2?
Changing the 6-element array to a different structure (e.g., a dictionary with face names).
