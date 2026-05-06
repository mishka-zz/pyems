import pytest
import json
from pathlib import Path
from pyems.config import load, ConfigError, SchemaVersionError, ValidationError, DielectricMaterialConfig, MicrostripPortConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_load_valid_fixture():
    cfg = load(FIXTURES_DIR / "single_port_microstrip.json")
    assert cfg.schema_version == 1
    assert cfg.simulation.freq_range == (1e9, 10e9)
    assert len(cfg.materials) == 2
    assert isinstance(cfg.materials[0], DielectricMaterialConfig)
    assert cfg.materials[0].name == "FR4"
    assert cfg.materials[0].epsilon == 4.4
    assert len(cfg.ports) == 1
    assert isinstance(cfg.ports[0], MicrostripPortConfig)

def test_load_unsupported_version(tmp_path):
    p = tmp_path / "bad_version.json"
    p.write_text(json.dumps({
        "schema_version": 2,
        "simulation": {"freq_range": [1e9, 10e9], "boundary_conditions": []}
    }))
    with pytest.raises(SchemaVersionError, match="Unsupported schema version: 2"):
        load(p)

def test_duplicate_material_name(tmp_path):
    p = tmp_path / "dup_mat.json"
    p.write_text(json.dumps({
        "schema_version": 1,
        "simulation": {
            "freq_range": [1e9, 10e9],
            "boundary_conditions": [{"type": "PEC"}] * 6
        },
        "materials": [
            {"name": "Copper", "kind": "metal"},
            {"name": "Copper", "kind": "metal", "source_label": "Duplicate"}
        ]
    }))
    with pytest.raises(ValidationError, match=r"Duplicate material name found: 'Copper' \(Duplicate\)"):
        load(p)

def test_unknown_material_reference(tmp_path):
    p = tmp_path / "bad_ref.json"
    p.write_text(json.dumps({
        "schema_version": 1,
        "simulation": {
            "freq_range": [1e9, 10e9],
            "boundary_conditions": [{"type": "PEC"}] * 6
        },
        "materials": [{"name": "Copper", "kind": "metal"}],
        "primitives": [{"type": "box", "material": "Gold", "start": [0,0,0], "stop": [1,1,1]}]
    }))
    with pytest.raises(ValidationError, match="references unknown material 'Gold'"):
        load(p)

def test_reserved_feature_warning(caplog):
    load(FIXTURES_DIR / "horn_antenna_nf2ff.json")
    assert "Feature 'nf2ff' is reserved in schema v1.0 but not yet implemented" in caplog.text

def test_load_missing_version(tmp_path):
    p = tmp_path / "no_version.json"
    p.write_text(json.dumps({
        "simulation": {"freq_range": [1e9, 10e9], "boundary_conditions": [{"type": "PEC"}] * 6}
    }))
    with pytest.raises(SchemaVersionError, match="The 'schema_version' field is missing"):
        load(p)

def test_schema_tightening_epsilon(tmp_path):
    p = tmp_path / "bad_epsilon.json"
    p.write_text(json.dumps({
        "schema_version": 1,
        "simulation": {
            "freq_range": [1e9, 10e9],
            "boundary_conditions": [{"type": "PEC"}] * 6
        },
        "materials": [{"name": "Copper", "kind": "metal", "epsilon": 4.4}]
    }))
    with pytest.raises(ValidationError, match="False schema does not allow"):
        load(p)

def test_schema_tightening_dielectric_value(tmp_path):
    p = tmp_path / "bad_dielectric_val.json"
    p.write_text(json.dumps({
        "schema_version": 1,
        "simulation": {
            "freq_range": [1e9, 10e9],
            "boundary_conditions": [{"type": "PEC"}] * 6
        },
        "materials": [{"name": "FR4", "kind": "dielectric", "epsilon": 0.5}]
    }))
    with pytest.raises(ValidationError, match="0.5 is less than the minimum of 1.0"):
        load(p)
