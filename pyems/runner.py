import json
import argparse
import numpy as np
import sys
import logging
import os
from pyems.simulation import Simulation
from pyems.mesh import Mesh
from pyems.boundary import BoundaryConditions
from pyems.coordinate import Box3, Coordinate3, Coordinate2, Axis
from pyems.field_dump import FieldDump, DumpType
from pyems.port import MicrostripPort, CoaxPort, DifferentialMicrostripPort, RectWaveguidePort
from pyems.csxcad import add_material, add_metal, add_conducting_sheet, construct_box, construct_cylinder, construct_polygon
from pyems.priority import priorities
import pyems.config

logging.basicConfig(level=logging.INFO)

DUMP_TYPE_MAP = {
    "E_TimeDomain": DumpType.efield_time,
    "H_TimeDomain": DumpType.hfield_time,
    "E_Frequency": DumpType.efield_frequency,
    "H_Frequency": DumpType.hfield_frequency,
    "J_TimeDomain": DumpType.current_density_time,
}


def _sanitize_marker_message(msg: str) -> str:
    """Sanitize message for stdout markers (single-line, quote-safe)."""
    return str(msg).replace("\n", " | ").replace('"', "'")


def parse_axis(axis_cfg: pyems.config.AxisConfig):
    return Axis(axis_cfg.axis, axis_cfg.direction)

def parse_box3(box_cfg: pyems.config.BoxConfig):
    return Box3(Coordinate3(*box_cfg.start.as_list()), Coordinate3(*box_cfg.stop.as_list()))

def run_simulation(config_path, validate_only=False):
    print("PYEMS:STARTED schema_version=1", flush=True)
    cfg = pyems.config.load(config_path)

    print(f"PYEMS:CONFIG_LOADED ports={len(cfg.ports)} primitives={len(cfg.primitives)} field_dumps={len(cfg.field_dumps)}", flush=True)

    if validate_only:
        print("Configuration is valid.", flush=True)
        print("PYEMS:DONE", flush=True)
        return

    sim_cfg = cfg.simulation
    freq = np.linspace(sim_cfg.freq_range[0], sim_cfg.freq_range[1], sim_cfg.num_freq_points)
    
    # Per-face boundary parsing
    bc_list = []
    for bc in sim_cfg.boundary_conditions:
        if bc.type == "PML":
            bc_list.append(f"PML_{bc.cells}")
        else:
            bc_list.append(bc.type)
    
    bc_tuple = (
        (bc_list[0], bc_list[1]),
        (bc_list[2], bc_list[3]),
        (bc_list[4], bc_list[5])
    )

    sim = Simulation(
        freq=freq,
        unit=sim_cfg.unit,
        reference_frequency=sim_cfg.reference_frequency,
        boundary_conditions=BoundaryConditions(bc_tuple),
        sim_dir=sim_cfg.sim_dir if sim_cfg.sim_dir else "sim_output",
        end_criteria=sim_cfg.end_criteria
    )
    
    props = {}
    for mat in cfg.materials:
        name = mat.name
        color = "#" + "".join(f"{c:02x}" for c in mat.color) if mat.color else None
        
        if isinstance(mat, pyems.config.DielectricMaterialConfig):
            props[name] = add_material(sim.csx, name=name, epsilon=mat.epsilon, kappa=mat.kappa, color=color)
        elif isinstance(mat, pyems.config.MetalMaterialConfig):
            props[name] = add_metal(sim.csx, name=name, color=color)
        elif isinstance(mat, pyems.config.ConductingSheetMaterialConfig):
            props[name] = add_conducting_sheet(sim.csx, name=name, conductivity=mat.conductivity, thickness=mat.thickness, color=color)
            
    for prim in cfg.primitives:
        prop = props[prim.material]
        priority = prim.priority if prim.priority is not None else priorities.get("trace", 4)
        
        if isinstance(prim, pyems.config.BoxPrimitiveConfig):
            construct_box(prop, Box3(Coordinate3(*prim.start.as_list()), Coordinate3(*prim.stop.as_list())), priority=priority)
        elif isinstance(prim, pyems.config.CylinderPrimitiveConfig):
            construct_cylinder(prop, start=prim.start.as_list(), stop=prim.stop.as_list(), radius=prim.radius, priority=priority)
        elif isinstance(prim, pyems.config.PolygonPrimitiveConfig):
            points = [Coordinate2(*p) for p in prim.points]
            construct_polygon(prop, points=points, normal=Axis(prim.normal), elevation=prim.elevation, priority=priority)

    # Lumped Elements
    for i, lumped in enumerate(cfg.lumped_elements):
        res = sim.csx.AddLumpedElement(
            name=f"lumped_{i}",
            ny=lumped.direction,
            R=lumped.R if lumped.R is not None else 0,
            L=lumped.L if lumped.L is not None else 0,
            C=lumped.C if lumped.C is not None else 0,
            caps=lumped.caps
        )
        construct_box(res, parse_box3(lumped.gap_box), priority=priorities.get("component", 10))
            
    for port in cfg.ports:
        num = port.number
        excite = port.excite
        
        if isinstance(port, pyems.config.MicrostripPortConfig):
            MicrostripPort(
                sim=sim,
                box=parse_box3(port.box),
                propagation_axis=parse_axis(port.propagation_axis),
                excitation_axis=parse_axis(port.excitation_axis),
                number=num,
                thickness=port.thickness,
                conductivity=port.conductivity,
                excite=excite,
                feed_shift=port.feed_shift,
                ref_impedance=port.ref_impedance,
                measurement_shift=port.measurement_shift
            )
        elif isinstance(port, pyems.config.CoaxialPortConfig):
            CoaxPort(
                sim=sim,
                number=num,
                start=Coordinate3(*port.start.as_list()),
                stop=Coordinate3(*port.stop.as_list()),
                radius=port.radius,
                core_radius=port.core_radius,
                excite=excite,
                feed_shift=port.feed_shift,
                measurement_shift=port.measurement_shift,
                delay=port.delay,
                ref_impedance=port.ref_impedance
            )
        # Note: RectWaveguide and DifferentialMS would go here if supported by runner

    if cfg.mesh:
        mesh_cfg = cfg.mesh
        Mesh(
            sim=sim,
            metal_res=mesh_cfg.metal_res if mesh_cfg.metal_res else 1/40,
            nonmetal_res=mesh_cfg.nonmetal_res if mesh_cfg.nonmetal_res else 1/10,
            smooth=mesh_cfg.smooth,
            min_lines=mesh_cfg.min_lines,
            expand_bounds=tuple(tuple(x) for x in mesh_cfg.expand_bounds)
        )
    
    if cfg.excitations:
        active_ports = set(cfg.excitations[0].active_ports)
        for port in sim.ports:
            port.excite = port.number in active_ports

    for fd_cfg in cfg.field_dumps:
        FieldDump(
            sim=sim,
            box=parse_box3(fd_cfg.box),
            dump_type=DUMP_TYPE_MAP[fd_cfg.type]
        )

    print("PYEMS:SIM_BUILT", flush=True)
    print(f"PYEMS:SOLVER_STARTED threads={sim_cfg.threads} sim_dir={sim.sim_dir}", flush=True)
    sim.run(threads=sim_cfg.threads)
    print("PYEMS:SOLVER_FINISHED", flush=True)
    
    print("PYEMS:POSTPROCESS_STARTED", flush=True)
    results = {}
    for port in sim.ports:
        z0 = np.abs(port.impedance())
        s11 = sim.s_param(port.number, port.number)
        results[f"port_{port.number}"] = {
            "z0": z0.tolist() if isinstance(z0, np.ndarray) else float(z0),
            "s11": s11.tolist() if isinstance(s11, np.ndarray) else float(s11)
        }
        for other_port in sim.ports:
            if other_port.number != port.number:
                s_other = sim.s_param(other_port.number, port.number)
                results[f"port_{port.number}"][f"s{other_port.number}{port.number}"] = s_other.tolist() if isinstance(s_other, np.ndarray) else float(s_other)
                
    results["frequency"] = sim.freq.tolist()
    
    output_path = os.path.join(sim.sim_dir, "results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"PYEMS:RESULTS {output_path}", flush=True)
    print("PYEMS:DONE", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to JSON simulation configuration")
    parser.add_argument("--validate-only", action="store_true", help="Only validate the configuration file")
    args = parser.parse_args()
    
    try:
        run_simulation(args.config, validate_only=args.validate_only)
    except pyems.config.ConfigError as e:
        msg = _sanitize_marker_message(e)
        print(f'PYEMS:ERROR kind=config message="{msg}"', flush=True)
        sys.exit(1)
    except Exception as e:
        msg = _sanitize_marker_message(e)
        print(f'PYEMS:ERROR kind=internal message="{msg}"', flush=True)
        sys.exit(2)
