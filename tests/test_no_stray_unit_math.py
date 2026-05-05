import os
from pathlib import Path

def test_no_inline_unit_scaling():
    """
    Conversion `* unit` or `* sim.unit` may only appear in csxcad.py.
    This enforces the 'Single Boundary Rule' defined in ADR 0007.
    """
    pyems_dir = Path("pyems")
    forbidden_files = [
        "port.py",
        "runner.py",
        "simulation.py",
        "mesh.py",
        "probe.py"
    ]
    
    violations = []
    
    for filename in forbidden_files:
        path = pyems_dir / filename
        if not path.exists():
            continue
            
        content = path.read_text()
        
        # Check for common scaling patterns
        # We look for multiplication by something that looks like the unit parameter
        patterns = ["* sim.unit", "* unit", "self.unit", ".unit"]
        
        # Filter: some uses of .unit are legit (assignment or property access)
        # We are specifically looking for multiplication or scaling math.
        
        lines = content.splitlines()
        for i, line in enumerate(lines):
            # Exception: docstrings are fine
            if ":param" in line or "Units are" in line:
                continue
                
            if "* sim.unit" in line or "* unit" in line:
                violations.append(f"{path}:{i+1}: {line.strip()}")

    assert not violations, f"Stray unit-scaling math found outside csxcad.py:\n" + "\n".join(violations)
