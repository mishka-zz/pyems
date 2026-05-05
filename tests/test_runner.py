import json
import os
import tempfile
import pytest
import numpy as np
from pyems.runner import run_simulation

@pytest.mark.parametrize("fixture_name", [
    "single_port_microstrip.json",
    "two_port_filter.json",
    "horn_antenna_nf2ff.json"
])
def test_validate_fixtures(fixture_name):
    """Fast test to ensure fixtures pass validation."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", fixture_name)
    run_simulation(fixture_path, validate_only=True)

@pytest.mark.slow
def test_headless_microstrip_slow():
    """Slow end-to-end test requiring openEMS. 
    Verifies the runner pipeline executes and produces sensible physics results.
    """
    with tempfile.TemporaryDirectory() as td:
        json_path = os.path.join(td, "test_config.json")
        sim_dir = os.path.join(td, "sim")
        
        # Geometry: 40x40mm substrate, 1.6mm thick. 3mm trace (approx 50 ohms).
        # Note: units are in meters (1.0) for this specific test case.
        config = {
            "schema_version": 1,
            "simulation": {
                "freq_range": [1e8, 2e9], # 100MHz to 2GHz
                "num_freq_points": 21,
                "unit": 1.0, 
                "end_criteria": 1e-3, # -30dB convergence
                "sim_dir": sim_dir,
                "boundary_conditions": [{"type": "PML", "cells": 8}] * 6
            },
            "mesh": {
                # Coarse mesh for fast smoke test in CI
                "metal_res": 0.002, 
                "nonmetal_res": 0.004,
                "smooth": [1.5, 1.5, 1.5],
                "min_lines": 5,
                "expand_bounds": [[10,10], [10,10], [10,10]]
            },
            "materials": [
                {"name": "FR4", "kind": "dielectric", "epsilon": 4.4},
                {"name": "Copper", "kind": "metal"} # PEC for speed/stability
            ],
            "primitives": [
                {
                    "material": "FR4",
                    "type": "box",
                    "start": [-0.02, -0.02, 0],
                    "stop": [0.02, 0.02, 0.0016],
                    "source_label": "Substrate"
                },
                {
                    "material": "Copper",
                    "type": "box",
                    "start": [-0.02, -0.02, -0.000035],
                    "stop": [0.02, 0.02, 0],
                    "source_label": "GroundPlane"
                },
                {
                    "material": "Copper",
                    "type": "box",
                    "start": [-0.017, -0.0015, 0.0016],
                    "stop": [0.02, 0.0015, 0.001635],
                    "source_label": "Trace"
                }
            ],
            "ports": [
                {
                    "type": "microstrip",
                    "number": 1,
                    "box": {"start": [-0.02, -0.0015, 0], "stop": [-0.017, 0.0015, 0.001635]},
                    "propagation_axis": {"axis": 0, "direction": 1},
                    "excitation_axis": {"axis": 2, "direction": 1},
                    "excite": True,
                    "thickness": 0.000035, # meters
                    "conductivity": 5.8e7,
                    "source_label": "Port1"
                }
            ],
            "excitations": [{"active_ports": [1]}]
        }
        
        with open(json_path, "w") as f:
            json.dump(config, f)
            
        run_simulation(json_path)
        
        out_path = "results.json" 
        assert os.path.exists(out_path)
        with open(out_path, "r") as f:
            res = json.load(f)
            
        assert "port_1" in res
        z0 = np.array(res["port_1"]["z0"])
        # Expecting approx 50 ohms for 3mm trace on 1.6mm FR4.
        # Coarse mesh might offset this, so we use a safe range.
        mean_z0 = np.mean(np.abs(z0))
        assert 40 < mean_z0 < 80, f"Expected Z0 in [40, 80], got {mean_z0}"

if __name__ == "__main__":
    test_headless_microstrip_slow()
    print("Test passed!")
