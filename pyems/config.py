import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional, Union, Any, Dict
import jsonschema

logger = logging.getLogger(__name__)

# --- Dataclasses for Structured Config ---

@dataclass(frozen=True)
class Coordinate3:
    x: float
    y: float
    z: float
    
    @classmethod
    def from_list(cls, l: List[float]):
        return cls(x=l[0], y=l[1], z=l[2])
    
    def as_list(self) -> List[float]:
        return [self.x, self.y, self.z]

@dataclass(frozen=True)
class BoxConfig:
    start: Coordinate3
    stop: Coordinate3

@dataclass(frozen=True)
class AxisConfig:
    axis: int
    direction: int

@dataclass(frozen=True)
class BoundaryConditionConfig:
    type: str
    cells: int = 8

@dataclass(frozen=True)
class SimulationConfig:
    freq_range: Tuple[float, float]
    num_freq_points: int
    waveform: str
    boundary_conditions: Tuple[BoundaryConditionConfig, ...]
    end_criteria: float
    timestep_factor: float
    unit: float
    sim_dir: Optional[str]
    threads: int
    reference_frequency: Optional[float]
    max_timesteps: int

@dataclass(frozen=True)
class MeshConfig:
    metal_res: Optional[float]
    nonmetal_res: Optional[float]
    smooth: Tuple[float, float, float]
    min_lines: int
    expand_bounds: Tuple[Tuple[int, int], ...]

# --- Materials ---

@dataclass(frozen=True)
class MaterialConfig:
    name: str
    kind: str
    color: Optional[List[int]] = None
    source_label: Optional[str] = None

@dataclass(frozen=True)
class DielectricMaterialConfig(MaterialConfig):
    epsilon: float = 1.0
    kappa: float = 0.0

@dataclass(frozen=True)
class MetalMaterialConfig(MaterialConfig):
    pass

@dataclass(frozen=True)
class ConductingSheetMaterialConfig(MaterialConfig):
    conductivity: float = 0.0
    thickness: float = 0.0

# --- Primitives ---

@dataclass(frozen=True)
class PrimitiveConfig:
    type: str
    material: str
    priority: Optional[int] = None
    source_label: Optional[str] = None

@dataclass(frozen=True)
class BoxPrimitiveConfig(PrimitiveConfig):
    start: Coordinate3 = field(default_factory=lambda: Coordinate3(0,0,0))
    stop: Coordinate3 = field(default_factory=lambda: Coordinate3(0,0,0))

@dataclass(frozen=True)
class CylinderPrimitiveConfig(PrimitiveConfig):
    start: Coordinate3 = field(default_factory=lambda: Coordinate3(0,0,0))
    stop: Coordinate3 = field(default_factory=lambda: Coordinate3(0,0,0))
    radius: float = 0.0

@dataclass(frozen=True)
class PolygonPrimitiveConfig(PrimitiveConfig):
    points: List[Tuple[float, float]] = field(default_factory=list)
    normal: int = 2
    elevation: float = 0.0

# --- Ports ---

@dataclass(frozen=True)
class PortConfig:
    type: str
    number: int
    excite: bool = False
    impedance: float = 50.0
    feed_shift: float = 0.2
    measurement_shift: float = 0.5
    ref_impedance: Optional[float] = None
    source_label: Optional[str] = None

@dataclass(frozen=True)
class LumpedPortConfig(PortConfig):
    # Note: Not yet fully implemented in runner but reserved in schema
    pass

@dataclass(frozen=True)
class MicrostripPortConfig(PortConfig):
    box: BoxConfig = field(default_factory=lambda: BoxConfig(Coordinate3(0,0,0), Coordinate3(0,0,0)))
    propagation_axis: AxisConfig = field(default_factory=lambda: AxisConfig(0, 1))
    excitation_axis: AxisConfig = field(default_factory=lambda: AxisConfig(2, 1))
    thickness: float = 0.035
    conductivity: float = 5.8e7

@dataclass(frozen=True)
class CoaxialPortConfig(PortConfig):
    start: Coordinate3 = field(default_factory=lambda: Coordinate3(0,0,0))
    stop: Coordinate3 = field(default_factory=lambda: Coordinate3(0,0,0))
    radius: float = 0.0
    core_radius: float = 0.0
    delay: float = 0.0

@dataclass(frozen=True)
class RectWaveguidePortConfig(PortConfig):
    box: BoxConfig = field(default_factory=lambda: BoxConfig(Coordinate3(0,0,0), Coordinate3(0,0,0)))
    propagation_axis: AxisConfig = field(default_factory=lambda: AxisConfig(0, 1))
    mode: str = "TE10"

@dataclass(frozen=True)
class DifferentialMicrostripPortConfig(PortConfig):
    trace_face_pos: BoxConfig = field(default_factory=lambda: BoxConfig(Coordinate3(0,0,0), Coordinate3(0,0,0)))
    trace_face_neg: BoxConfig = field(default_factory=lambda: BoxConfig(Coordinate3(0,0,0), Coordinate3(0,0,0)))
    ground_reference: BoxConfig = field(default_factory=lambda: BoxConfig(Coordinate3(0,0,0), Coordinate3(0,0,0)))
    thickness: float = 0.035
    conductivity: float = 5.8e7
    propagation_axis: AxisConfig = field(default_factory=lambda: AxisConfig(0, 1))

# --- Others ---

@dataclass(frozen=True)
class LumpedElementConfig:
    direction: int
    gap_box: BoxConfig
    R: Optional[float] = None
    L: Optional[float] = None
    C: Optional[float] = None
    caps: bool = True
    source_label: Optional[str] = None

@dataclass(frozen=True)
class ExcitationConfig:
    active_ports: List[int]
    amplitude: Optional[float] = None
    phase: Optional[float] = None

@dataclass(frozen=True)
class Config:
    schema_version: int
    simulation: SimulationConfig
    mesh: Optional[MeshConfig] = None
    materials: Tuple[MaterialConfig, ...] = field(default_factory=tuple)
    primitives: Tuple[PrimitiveConfig, ...] = field(default_factory=tuple)
    ports: Tuple[PortConfig, ...] = field(default_factory=tuple)
    lumped_elements: Tuple[LumpedElementConfig, ...] = field(default_factory=tuple)
    excitations: Tuple[ExcitationConfig, ...] = field(default_factory=tuple)
    mesh_lines: List[Dict[str, Any]] = field(default_factory=list)
    mesh_regions: List[Dict[str, Any]] = field(default_factory=list)
    nf2ff: List[Dict[str, Any]] = field(default_factory=list)
    field_dumps: List[Dict[str, Any]] = field(default_factory=list)
    probes: List[Dict[str, Any]] = field(default_factory=list)
    pcb_stackup: Optional[Dict[str, Any]] = None

class ConfigError(Exception): pass
class SchemaVersionError(ConfigError): pass
class ValidationError(ConfigError): pass

IMPLEMENTED_FEATURES = {
    "simulation", "mesh", "materials", "primitives", "ports", "lumped_elements", "excitations"
}

RESERVED_FEATURES = {
    "mesh_lines", "mesh_regions", "nf2ff", "field_dumps", "probes", "pcb_stackup"
}

def load(path: Union[str, Path]) -> Config:
    path = Path(path)
    with open(path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Failed to parse JSON: {e}")

    # 1. Validate against schema
    schema_path = Path(__file__).parent.parent / "schema" / "v1.json"
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        # Check for schema_version explicitly
        if e.validator == "const" and e.path and e.path[0] == "schema_version":
             raise SchemaVersionError(f"Unsupported schema version: {e.instance}. Only version 1 is supported.")
        if e.validator == "required" and "schema_version" in e.message:
             raise SchemaVersionError("The 'schema_version' field is missing from the configuration.")
        raise ValidationError(f"Schema validation failed at {e.json_path}: {e.message}")

    # 2. Warn about reserved but unimplemented features
    for feature in RESERVED_FEATURES:
        if feature in data and data[feature]:
            logger.warning(f"Feature '{feature}' is reserved in schema v1.0 but not yet implemented in the runner. It will be ignored.")

    # 3. Material name uniqueness (B3)
    material_names = []
    for m in data.get("materials", []):
        name = m["name"]
        if name in material_names:
            label = f" ({m['source_label']})" if "source_label" in m else ""
            raise ValidationError(f"Duplicate material name found: '{name}'{label}")
        material_names.append(name)
    material_names_set = set(material_names)

    # 4. FK Validation: Primitive materials
    for i, prim in enumerate(data.get("primitives", [])):
        if prim["material"] not in material_names_set:
            label = f" ({prim['source_label']})" if "source_label" in prim else ""
            raise ValidationError(f"Primitive {i}{label} references unknown material '{prim['material']}'")

    # 5. Parse into dataclasses
    sim_data = data["simulation"]
    simulation = SimulationConfig(
        freq_range=tuple(sim_data["freq_range"]),
        num_freq_points=sim_data.get("num_freq_points", 501),
        waveform=sim_data.get("waveform", "Gaussian"),
        boundary_conditions=tuple(
            BoundaryConditionConfig(type=bc["type"], cells=bc.get("cells", 8))
            for bc in sim_data["boundary_conditions"]
        ),
        end_criteria=sim_data.get("end_criteria", 1e-5),
        timestep_factor=sim_data.get("timestep_factor", 1.0),
        unit=sim_data.get("unit", 1e-3),
        sim_dir=sim_data.get("sim_dir"),
        threads=sim_data.get("threads", 0),
        reference_frequency=sim_data.get("reference_frequency"),
        max_timesteps=sim_data.get("max_timesteps", 1000000)
    )

    mesh = None
    if "mesh" in data:
        m_data = data["mesh"]
        mesh = MeshConfig(
            metal_res=m_data.get("metal_res"),
            nonmetal_res=m_data.get("nonmetal_res"),
            smooth=tuple(m_data.get("smooth", [1.2, 1.2, 1.2])),
            min_lines=m_data.get("min_lines", 5),
            expand_bounds=tuple(tuple(b) for b in m_data.get("expand_bounds", [[8,8],[8,8],[8,8]]))
        )

    materials = []
    for m in data.get("materials", []):
        kind = m["kind"]
        base_args = {
            "name": m["name"],
            "kind": kind,
            "color": m.get("color"),
            "source_label": m.get("source_label")
        }
        if kind == "dielectric":
            materials.append(DielectricMaterialConfig(**base_args, epsilon=m["epsilon"], kappa=m.get("kappa", 0.0)))
        elif kind == "metal":
            materials.append(MetalMaterialConfig(**base_args))
        elif kind == "conducting_sheet":
            materials.append(ConductingSheetMaterialConfig(**base_args, conductivity=m["conductivity"], thickness=m["thickness"]))

    primitives = []
    for p in data.get("primitives", []):
        ptype = p["type"]
        base_args = {
            "type": ptype,
            "material": p["material"],
            "priority": p.get("priority"),
            "source_label": p.get("source_label")
        }
        if ptype == "box":
            primitives.append(BoxPrimitiveConfig(**base_args, start=Coordinate3.from_list(p["start"]), stop=Coordinate3.from_list(p["stop"])))
        elif ptype == "cylinder":
            primitives.append(CylinderPrimitiveConfig(**base_args, start=Coordinate3.from_list(p["start"]), stop=Coordinate3.from_list(p["stop"]), radius=p["radius"]))
        elif ptype == "polygon":
            primitives.append(PolygonPrimitiveConfig(**base_args, points=[tuple(pt) for pt in p["points"]], normal=p["normal"], elevation=p["elevation"]))

    ports = []
    for p in data.get("ports", []):
        ptype = p["type"]
        base_args = {
            "type": ptype,
            "number": p["number"],
            "excite": p.get("excite", False),
            "impedance": p.get("impedance", 50.0),
            "feed_shift": p.get("feed_shift", 0.2),
            "measurement_shift": p.get("measurement_shift", 0.5),
            "ref_impedance": p.get("ref_impedance"),
            "source_label": p.get("source_label")
        }
        if ptype == "microstrip":
            ports.append(MicrostripPortConfig(
                **base_args,
                box=BoxConfig(Coordinate3.from_list(p["box"]["start"]), Coordinate3.from_list(p["box"]["stop"])),
                propagation_axis=AxisConfig(p["propagation_axis"]["axis"], p["propagation_axis"]["direction"]),
                excitation_axis=AxisConfig(p["excitation_axis"]["axis"], p["excitation_axis"]["direction"]),
                thickness=p["thickness"],
                conductivity=p.get("conductivity", 5.8e7)
            ))
        elif ptype == "coaxial":
            ports.append(CoaxialPortConfig(
                **base_args,
                start=Coordinate3.from_list(p["start"]),
                stop=Coordinate3.from_list(p["stop"]),
                radius=p["radius"],
                core_radius=p["core_radius"],
                delay=p.get("delay", 0.0)
            ))
        elif ptype == "rect_waveguide":
            ports.append(RectWaveguidePortConfig(
                **base_args,
                box=BoxConfig(Coordinate3.from_list(p["box"]["start"]), Coordinate3.from_list(p["box"]["stop"])),
                propagation_axis=AxisConfig(p["propagation_axis"]["axis"], p["propagation_axis"]["direction"]),
                mode=p.get("mode", "TE10")
            ))
        elif ptype == "differential_microstrip":
            ports.append(DifferentialMicrostripPortConfig(
                **base_args,
                trace_face_pos=BoxConfig(Coordinate3.from_list(p["trace_face_pos"]["start"]), Coordinate3.from_list(p["trace_face_pos"]["stop"])),
                trace_face_neg=BoxConfig(Coordinate3.from_list(p["trace_face_neg"]["start"]), Coordinate3.from_list(p["trace_face_neg"]["stop"])),
                ground_reference=BoxConfig(Coordinate3.from_list(p["ground_reference"]["start"]), Coordinate3.from_list(p["ground_reference"]["stop"])),
                thickness=p["thickness"],
                conductivity=p.get("conductivity", 5.8e7),
                propagation_axis=AxisConfig(p["propagation_axis"]["axis"], p["propagation_axis"]["direction"])
            ))
        elif ptype == "lumped":
             ports.append(LumpedPortConfig(**base_args))

    lumped_elements = []
    for l in data.get("lumped_elements", []):
        lumped_elements.append(LumpedElementConfig(
            direction=l["direction"],
            gap_box=BoxConfig(Coordinate3.from_list(l["gap_box"]["start"]), Coordinate3.from_list(l["gap_box"]["stop"])),
            R=l.get("R"),
            L=l.get("L"),
            C=l.get("C"),
            caps=l.get("caps", True),
            source_label=l.get("source_label")
        ))

    excitations = []
    for e in data.get("excitations", []):
        excitations.append(ExcitationConfig(
            active_ports=e["active_ports"],
            amplitude=e.get("amplitude"),
            phase=e.get("phase")
        ))

    return Config(
        schema_version=data["schema_version"],
        simulation=simulation,
        mesh=mesh,
        materials=tuple(materials),
        primitives=tuple(primitives),
        ports=tuple(ports),
        lumped_elements=tuple(lumped_elements),
        excitations=tuple(excitations),
        mesh_lines=data.get("mesh_lines", []),
        mesh_regions=data.get("mesh_regions", []),
        nf2ff=data.get("nf2ff", []),
        field_dumps=data.get("field_dumps", []),
        probes=data.get("probes", []),
        pcb_stackup=data.get("pcb_stackup")
    )
