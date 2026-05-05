# pyems Runner CLI Contract

This document defines the stable interface for invoking the `pyems` runner as a subprocess.

## Exit Codes

- `0` — Success. Simulation completed and results written.
- `1` — `ConfigError` (including `SchemaVersionError` and `ValidationError`). The input configuration is invalid.
- `2` — Internal or Runtime Error. Includes solver crashes, unhandled translation cases, or other unexpected Python exceptions.

## Stdout Markers (`PYEMS:`)

The runner emits structured marker lines on stdout to allow the caller to track lifecycle events. All markers are prefixed with `PYEMS:`.

| Marker | Description |
| :--- | :--- |
| `PYEMS:STARTED schema_version=1` | Runner started and identified the schema version. |
| `PYEMS:CONFIG_LOADED ports=N primitives=M field_dumps=D` | Configuration loaded and parsed successfully. |
| `PYEMS:SIM_BUILT` | Simulation model built in CSXCAD. |
| `PYEMS:SOLVER_STARTED threads=T sim_dir=PATH` | openEMS solver has started. `sim_dir` is an absolute path. |
| `PYEMS:SOLVER_FINISHED` | openEMS solver has finished. |
| `PYEMS:POSTPROCESS_STARTED` | Post-processing (e.g. S-parameter calculation) started. |
| `PYEMS:RESULTS PATH` | Simulation results written to `results.json` at the specified absolute path. |
| `PYEMS:DONE` | Runner finished successfully. |
| `PYEMS:ERROR kind=K message="MSG"` | An error occurred. `kind` is one of `{config|internal}`. |

**Note:** All stdout is flushed immediately after each marker line. Free-form text (e.g. from openEMS or Python warnings) may appear between markers and should be displayed to the user but not parsed for state tracking.

### Marker Parsing Rules

- **Single-line:** Marker lines never contain newlines. In `PYEMS:ERROR` messages, original newlines are normalized to ` | `.
- **Quote-safe:** In `PYEMS:ERROR` messages, embedded double quotes are normalized to `'` to ensure the `message="..."` attribute is unambiguous.
- **Space handling:** For markers with values (like `PYEMS:RESULTS <path>` or `PYEMS:ERROR ... message="msg"`), the value is the rest of the line (or the content between quotes). Do not split on whitespace if the value itself can contain spaces.

## Result Location

By default, results are written to `<sim_dir>/results.json`.
- `sim_dir` is defined in the input JSON (`simulation.sim_dir`).
- If `sim_dir` is not provided, it defaults to `sim_output` in the runner's CWD.
- The runner always resolves `sim_dir` to an absolute path before use.

## Field Dumps

If `field_dumps` are defined in the configuration, openEMS will write `.vtr` (VTK Rectilinear Grid) files into subdirectories of `sim_dir`. These files can be opened in ParaView for visualization.
