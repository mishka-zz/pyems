import pytest
import numpy as np
from pyems.simulation import Simulation
from pyems.coordinate import Box3, Coordinate3, Axis
from pyems.port import MicrostripPort, DifferentialMicrostripPort
from pyems.csxcad import add_conducting_sheet
from CSXCAD.CSXCAD import ContinuousStructure

def test_add_conducting_sheet_scaling():
    """Verify that thickness is correctly scaled to absolute meters in CSXCAD."""
    csx = ContinuousStructure()
    unit = 1e-3 # mm
    csx.GetGrid().SetDeltaUnit(unit)
    
    # 1. Test direct call
    prop = add_conducting_sheet(csx, "TestSheet", conductivity=5.8e7, thickness=0.035)
    # 0.035 mm * 1e-3 = 3.5e-5 meters
    assert prop.GetThickness() == pytest.approx(3.5e-5)
    
    # 2. Test via MicrostripPort
    sim = Simulation(freq=np.linspace(1e9, 10e9, 11), unit=unit)
    port = MicrostripPort(
        sim=sim,
        box=Box3(Coordinate3(0,0,0), Coordinate3(10,1,1)),
        propagation_axis=Axis(0),
        excitation_axis=Axis(2),
        number=1,
        thickness=0.035
    )
    # Find the property created for the port trace
    # MicrostripPort names its trace "Microstrip_Trace_" + str(self.number)
    prop = sim.csx.GetPropertiesByName("Microstrip_Trace_1")[0]
    assert prop.GetThickness() == pytest.approx(3.5e-5)
    
    # 3. Test via DifferentialMicrostripPort
    DifferentialMicrostripPort(
        sim=sim,
        box=Box3(Coordinate3(0,0,1), Coordinate3(10,5,1)),
        propagation_axis=Axis(0),
        excitation_axis=Axis(1),
        number=2,
        gap=1.0,
        thickness=0.035
    )
    prop = sim.csx.GetPropertiesByName("Differential_Microstrip_Trace_2")[0]
    assert prop.GetThickness() == pytest.approx(3.5e-5)

def test_unit_scaling_consistency():
    """Verify that different units result in the same absolute meters."""
    for unit in [1.0, 1e-3, 1e-6]:
        csx = ContinuousStructure()
        csx.GetGrid().SetDeltaUnit(unit)
        
        # We want to represent 35 micrometers
        thickness_in_units = 35e-6 / unit
        
        prop = add_conducting_sheet(csx, "ScaleTest", 5.8e7, thickness_in_units)
        assert prop.GetThickness() == pytest.approx(3.5e-5)

def test_csxcad_is_the_scaling_boundary():
    """Sentinel: scaling MUST happen inside add_conducting_sheet.
    This provides a positive assertion to complement the negative lint test
    in tests/test_no_stray_unit_math.py.
    """
    from pathlib import Path
    src = (Path(__file__).parent.parent / "pyems" / "csxcad.py").read_text()
    assert "GetDeltaUnit" in src and "thickness * unit" in src, \
        "csxcad.add_conducting_sheet lost its unit-scaling boundary logic"
