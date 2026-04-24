"""Common types for parametric models."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Cut:
    """A single piece of dimensional lumber to cut."""
    name: str            # human-readable role, e.g. "shelf"
    nominal: str         # e.g. "1x12", "2x4"
    length_in: float
    qty: int = 1
    notes: str = ""


@dataclass
class PanelCut:
    """A piece cut from a sheet good (plywood/OSB)."""
    name: str
    thickness_in: float
    length_in: float    # longer dimension
    width_in: float
    qty: int = 1
    notes: str = ""


@dataclass
class HardwareNeed:
    catalog_id: str
    qty: int
    notes: str = ""


@dataclass
class Part3D:
    """Axis-aligned box for the 3D preview. Units: inches."""
    label: str
    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float
    color: str = "#c69c6d"


@dataclass
class Build:
    cuts: list[Cut] = field(default_factory=list)
    panels: list[PanelCut] = field(default_factory=list)
    hardware: list[HardwareNeed] = field(default_factory=list)
    parts_3d: list[Part3D] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # Per-step assembly hints, used by the instruction generator to add detail.
    assembly_hints: dict[str, Any] = field(default_factory=dict)


class ParamSpec:
    """Tiny parameter spec the frontend can render as a form."""
    def __init__(self, key: str, label: str, kind: str, default,
                 min_val=None, max_val=None, step=None, unit: str = "",
                 help: str = "", choices: list | None = None):
        self.key = key
        self.label = label
        self.kind = kind  # "number" | "integer" | "choice" | "boolean"
        self.default = default
        self.min = min_val
        self.max = max_val
        self.step = step
        self.unit = unit
        self.help = help
        self.choices = choices

    def to_dict(self) -> dict:
        d = {
            "key": self.key,
            "label": self.label,
            "kind": self.kind,
            "default": self.default,
            "unit": self.unit,
            "help": self.help,
        }
        if self.min is not None: d["min"] = self.min
        if self.max is not None: d["max"] = self.max
        if self.step is not None: d["step"] = self.step
        if self.choices is not None: d["choices"] = self.choices
        return d


class ProjectModel:
    id: str = ""
    name: str = ""
    description: str = ""
    difficulty: str = "Beginner"  # Beginner | Intermediate | Advanced
    estimated_time_hours: float = 4.0
    params: list[ParamSpec] = []

    @classmethod
    def schema(cls) -> dict:
        return {
            "id": cls.id,
            "name": cls.name,
            "description": cls.description,
            "difficulty": cls.difficulty,
            "estimated_time_hours": cls.estimated_time_hours,
            "parameters": [p.to_dict() for p in cls.params],
        }

    @classmethod
    def coerce(cls, raw: dict) -> dict:
        """Apply defaults and coerce types from incoming JSON."""
        out = {}
        for p in cls.params:
            v = raw.get(p.key, p.default)
            if p.kind == "number":
                v = float(v)
                if p.min is not None: v = max(p.min, v)
                if p.max is not None: v = min(p.max, v)
            elif p.kind == "integer":
                v = int(v)
                if p.min is not None: v = max(p.min, v)
                if p.max is not None: v = min(p.max, v)
            elif p.kind == "boolean":
                v = bool(v)
            out[p.key] = v
        return out

    @classmethod
    def generate(cls, params: dict) -> Build:
        raise NotImplementedError
