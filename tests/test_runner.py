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
        
        # Geometry: 200x30mm substrate, 1.6mm thick. 3mm trace (approx 50 ohms).
        # This matches fixtures/single_port_microstrip.json exactly.
        config = {
            "schema_version": 1,
            "simulation": {
                "freq_range": [1e9, 10e9],
                "num_freq_points": 101,
                "unit": 1e-3, 
                "timestep_factor": 0.9,
                "end_criteria": 1e-4, 
                "sim_dir": sim_dir,
                "boundary_conditions": [{"type": "PML", "cells": 8}] * 6
            },
            "mesh": {
                "metal_res": 0.05, 
                "nonmetal_res": 0.1,
                "smooth": [1.2, 1.2, 1.2],
                "min_lines": 3,
                "expand_bounds": [[0, 0], [10, 10], [10, 10]]
            },
            "materials": [
                {"name": "FR4", "kind": "dielectric", "epsilon": 4.4},
                {"name": "Copper", "kind": "metal"}
            ],
            "primitives": [
                {
                    "material": "FR4",
                    "type": "box",
                    "priority": 0,
                    "start": [-100, -15, 0],
                    "stop": [100, 15, 1.6],
                    "source_label": "Substrate"
                },
                {
                    "material": "Copper",
                    "type": "box",
                    "priority": 1,
                    "start": [-100, -15, 0],
                    "stop": [100, 15, 0],
                    "source_label": "GroundPlane"
                }
            ],
            "ports": [
                {
                    "type": "microstrip",
                    "number": 1,
                    "excite": True,
                    "box": {"start": [-100, -1.5, 0], "stop": [100, 1.5, 1.6]},
                    "propagation_axis": {"axis": 0, "direction": 1},
                    "excitation_axis": {"axis": 2, "direction": 1},
                    "thickness": 0.035,
                    "conductivity": 5.8e7,
                    "source_label": "Port1"
                }
            ],
            "excitations": [{"active_ports": [1]}]
        }
        
        with open(json_path, "w") as f:
            json.dump(config, f)
            
        run_simulation(json_path)
        
        out_path = os.path.join(sim_dir, "results.json")
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
