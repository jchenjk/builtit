"""Workbench parametric model.

A solid shop workbench: 2x4 legs and frames, a double-layer 3/4" plywood
top, and an optional lower shelf. The first thing to build if you plan to
build anything else.

Geometry: X = width, Y = depth, Z = height.
"""
import math
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class WorkbenchModel(ProjectModel):
    id = "workbench"
    name = "Workbench"
    description = ("A sturdy 2x4 workbench with a double-thick plywood top "
                   "and lower shelf. Build this first — every other project "
                   "gets easier on a real bench.")
    difficulty = "Beginner"
    estimated_time_hours = 5.0
    params = [
        ParamSpec("width_in", "Width", "number", 60,
                  min_val=48, max_val=96, step=4, unit="in"),
        ParamSpec("depth_in", "Depth", "number", 24,
                  min_val=20, max_val=30, step=2, unit="in"),
        ParamSpec("height_in", "Height", "number", 36,
                  min_val=32, max_val=40, step=1, unit="in",
                  help="Rule of thumb: the crease of your wrist standing upright."),
        ParamSpec("lower_shelf", "Lower shelf", "boolean", True),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        D = p["depth_in"]
        H = p["height_in"]
        SHELF = p["lower_shelf"]

        T = 1.5
        FW = 3.5
        TOP_T = 1.5  # two layers of 3/4 ply

        b = Build()

        # --- Cuts ---
        leg_h = H - TOP_T
        b.cuts.append(Cut("Leg", "2x4", leg_h, qty=4))
        # Top frame: 2 long + cross members every 16"
        n_cross = max(2, int(math.ceil(W / 16)) + 1)
        b.cuts.append(Cut("Top frame rail (long)", "2x4", W, qty=2))
        b.cuts.append(Cut("Top frame cross member", "2x4", D - 2 * T, qty=n_cross))
        # Lower frame (also stiffens the legs)
        b.cuts.append(Cut("Lower rail (long)", "2x4", W - 2 * T, qty=2))
        b.cuts.append(Cut("Lower rail (short)", "2x4", D - 2 * T, qty=2))
        # Top: two layers of 3/4 plywood
        b.panels.append(PanelCut("Benchtop layer", thickness_in=0.75,
                                 length_in=W, width_in=D, qty=2,
                                 notes="Glue + screw two layers into one 1-1/2\" slab."))
        if SHELF:
            b.panels.append(PanelCut("Lower shelf", thickness_in=0.75,
                                     length_in=W - 2 * T, width_in=D - 2 * T, qty=1))

        # --- Hardware ---
        b.hardware.append(HardwareNeed("fastener.screws.deck.3in.5lb", 1,
                                       notes="Frame and leg joints."))
        b.hardware.append(HardwareNeed("fastener.screws.wood.1.25in.1lb", 1,
                                       notes="Laminating the two top layers."))
        b.hardware.append(HardwareNeed("finish.woodglue.16oz", 1))
        b.hardware.append(HardwareNeed("finish.sandpaper.assorted", 1))

        # --- 3D preview ---
        for (x, y) in [(1, 1), (W - FW - 1, 1), (1, D - FW - 1), (W - FW - 1, D - FW - 1)]:
            b.parts_3d.append(Part3D("Leg", x, y, 0, FW, FW, leg_h, "#8b5a2b"))
        # Top frame + top
        b.parts_3d.append(Part3D("Top frame front", 0, 0, leg_h - FW, W, T, FW, "#a87b4f"))
        b.parts_3d.append(Part3D("Top frame back", 0, D - T, leg_h - FW, W, T, FW, "#a87b4f"))
        b.parts_3d.append(Part3D("Benchtop", 0, 0, leg_h, W, D, TOP_T, "#d6b48a"))
        # Lower rails + shelf
        shelf_z = 6
        b.parts_3d.append(Part3D("Lower rail front", 1, 1, shelf_z, W - 2, T, FW, "#a87b4f"))
        b.parts_3d.append(Part3D("Lower rail back", 1, D - T - 1, shelf_z, W - 2, T, FW, "#a87b4f"))
        if SHELF:
            b.parts_3d.append(Part3D("Lower shelf", 1, 1, shelf_z + FW,
                                     W - 2, D - 2, 0.75, "#c69c6d"))

        b.notes.append("Flatten the top: run a straightedge across it and shim between the "
                       "layers before final screwing if needed.")
        b.notes.append("Bolt a vise to a front corner when budget allows — it doubles the bench's usefulness.")
        b.assembly_hints = {
            "width_in": W, "depth_in": D, "height_in": H,
            "lower_shelf": SHELF, "n_cross": n_cross, "leg_height_in": round(leg_h, 2),
        }
        return b
