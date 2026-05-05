import json
import os
import subprocess
import tempfile
import sys
import pytest
from pyems.runner import run_simulation, _sanitize_marker_message
import pyems.config

@pytest.fixture
def microstrip_fixture():
    return os.path.join(os.path.dirname(__file__), "fixtures", "single_port_microstrip.json")

@pytest.fixture
def microstrip_with_dump_fixture():
    return os.path.join(os.path.dirname(__file__), "fixtures", "single_port_microstrip_with_dump.json")

@pytest.fixture
def env():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return env

def test_sanitize_marker_message():
    """E3: Test the sanitization helper directly."""
    assert _sanitize_marker_message("line1\nline2") == "line1 | line2"
    assert _sanitize_marker_message('error in "field"') == "error in 'field'"
    assert _sanitize_marker_message('multi\n"quoted"') == "multi | 'quoted'"

@pytest.mark.slow
def test_results_location_is_sim_dir(env):
    """E1: Assert the result file is in sim_dir and not in CWD when run from a different CWD.
    Slow — invokes openEMS.
    """
    with tempfile.TemporaryDirectory() as td:
        sim_dir = os.path.join(td, "my_sim")
        config_path = os.path.join(td, "config.json")
        
        # Create a config with a specific sim_dir
        with open(os.path.join(os.path.dirname(__file__), "fixtures", "single_port_microstrip.json"), 'r') as f:
            data = json.load(f)
        data["simulation"]["sim_dir"] = sim_dir
        with open(config_path, 'w') as f:
            json.dump(data, f)
            
        # Run from a different temporary directory as CWD
        cwd = os.path.join(td, "cwd")
        os.mkdir(cwd)
        
        # We need to use absolute path for config_path since we change CWD
        abs_config_path = os.path.abspath(config_path)
        
        # Use sys.executable to ensure portability
        subprocess.run([sys.executable, "-m", "pyems.runner", abs_config_path], cwd=cwd, env=env, check=True)
        
        assert os.path.exists(os.path.join(sim_dir, "results.json"))
        assert not os.path.exists(os.path.join(cwd, "results.json"))

def test_stdout_markers_validate_only(microstrip_fixture, env):
    """E3: Capture stdout from --validate-only, assert markers and their order."""
    result = subprocess.run(
        [sys.executable, "-m", "pyems.runner", "--validate-only", microstrip_fixture],
        capture_output=True, text=True, env=env, check=True
    )
    stdout = result.stdout
    assert "PYEMS:STARTED schema_version=1" in stdout
    assert "PYEMS:CONFIG_LOADED" in stdout
    assert "PYEMS:DONE" in stdout
    assert "Configuration is valid." in stdout
    
    # Assert marker order
    i_started = stdout.index("PYEMS:STARTED")
    i_loaded = stdout.index("PYEMS:CONFIG_LOADED")
    i_done = stdout.index("PYEMS:DONE")
    assert i_started < i_loaded < i_done

def test_stdout_error_on_corrupt_fixture(env):
    """E3: Corrupt fixture (drop schema_version) emits PYEMS:ERROR and exits 1."""
    with tempfile.TemporaryDirectory() as td:
        config_path = os.path.join(td, "corrupt.json")
        # Missing required schema_version and simulation
        with open(config_path, 'w') as f:
            json.dump({"something": "else"}, f)
            
        result = subprocess.run(
            [sys.executable, "-m", "pyems.runner", config_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 1
        assert "PYEMS:ERROR kind=config" in result.stdout

def test_stdout_error_is_single_line(env):
    """E3: Robustly verify that even multi-line schema errors are emitted as a single line."""
    with tempfile.TemporaryDirectory() as td:
        config_path = os.path.join(td, "bad_schema.json")
        # Trigger a complex jsonschema error
        with open(config_path, 'w') as f:
            json.dump({
                "schema_version": 1,
                "simulation": "should be an object"
            }, f)
            
        result = subprocess.run(
            [sys.executable, "-m", "pyems.runner", config_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 1
        
        # Verify single PYEMS:ERROR token and single line ending with quote
        assert result.stdout.count("PYEMS:ERROR") == 1
        idx = result.stdout.find("PYEMS:ERROR")
        eol = result.stdout.find("\n", idx)
        marker_line = result.stdout[idx : eol if eol != -1 else len(result.stdout)]
        
        # Ensure the marker line itself contains no newlines (redundant but explicit)
        assert "\n" not in marker_line
        # Ensure it ends with a closing quote
        assert marker_line.endswith('"')
        # message="..." content should not contain "
        message_content = marker_line[ marker_line.find('message="') + 9 : -1 ]
        assert '"' not in message_content

def test_stdout_internal_error(env):
    """E3: Internal error path (e.g. parallel axes) emits kind=internal and exits 2.
    Fast — error fires in MicrostripPort.__init__, before sim.run() is called.
    """
    with tempfile.TemporaryDirectory() as td:
        config_path = os.path.join(td, "internal_err.json")
        with open(os.path.join(os.path.dirname(__file__), "fixtures", "single_port_microstrip.json"), 'r') as f:
            data = json.load(f)
        
        # Force parallel axes which causes ValueError in MicrostripPort
        data["ports"][0]["propagation_axis"]["axis"] = 0
        data["ports"][0]["excitation_axis"]["axis"] = 0
        
        with open(config_path, 'w') as f:
            json.dump(data, f)
            
        result = subprocess.run(
            [sys.executable, "-m", "pyems.runner", config_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 2
        assert "PYEMS:ERROR kind=internal" in result.stdout
        assert "Excitation and propagation axes must be perpendicular." in result.stdout

@pytest.mark.slow
def test_field_dump_produces_vtr(microstrip_with_dump_fixture, env):
    """E2: Runs fixture with field dump and asserts at least one .vtr file exists.
    Slow — invokes openEMS.
    """
    with tempfile.TemporaryDirectory() as td:
        sim_dir = os.path.join(td, "sim_dump")
        config_path = os.path.join(td, "config.json")
        
        with open(microstrip_with_dump_fixture, 'r') as f:
            data = json.load(f)
        data["simulation"]["sim_dir"] = sim_dir
        with open(config_path, 'w') as f:
            json.dump(data, f)
            
        subprocess.run([sys.executable, "-m", "pyems.runner", config_path], env=env, check=True)
        
        # FieldDump usually creates subdirectories like dump_0/Et.vtr or similar
        vtr_files = []
        for root, dirs, files in os.walk(sim_dir):
            for file in files:
                if file.endswith(".vtr"):
                    vtr_files.append(os.path.join(root, file))
        
        assert len(vtr_files) > 0, f"No .vtr files found in {sim_dir}"

def test_config_parses_all_dump_types():
    """E2: Verify all five enum strings are parsed correctly."""
    dump_types = ["E_TimeDomain", "H_TimeDomain", "E_Frequency", "H_Frequency", "J_TimeDomain"]
    
    with tempfile.TemporaryDirectory() as td:
        for dt in dump_types:
            config_data = {
                "schema_version": 1,
                "simulation": {
                    "freq_range": [1e9, 10e9],
                    "boundary_conditions": [{"type": "PEC"}] * 6
                },
                "field_dumps": [
                    {
                        "type": dt,
                        "box": {"start": [0,0,0], "stop": [1,1,1]}
                    }
                ]
            }
            config_path = os.path.join(td, f"{dt}.json")
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            cfg = pyems.config.load(config_path)
            assert cfg.field_dumps[0].type == dt

def test_no_reserved_feature_warning_for_field_dumps(caplog, microstrip_with_dump_fixture):
    """E2: Reserved-feature warning should no longer fire for field_dumps."""
    import logging
    with caplog.at_level(logging.WARNING):
        pyems.config.load(microstrip_with_dump_fixture)
    
    assert "Feature 'field_dumps' is reserved" not in caplog.text
