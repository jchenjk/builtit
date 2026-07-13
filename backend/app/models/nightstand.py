"""Nightstand parametric model.

A compact bedside cabinet from 1x12 pine: two sides, top, bottom, one
mid shelf, and a 1/2" plywood back. Same joinery as the bookshelf but
sized for a bedside — a perfect second project.

Geometry: X = width, Y = depth (11.25" from 1x12), Z = height.
"""
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class NightstandModel(ProjectModel):
    id = "nightstand"
    name = "Nightstand"
    description = ("A compact bedside cabinet from 1x12 pine with an open "
                   "cubby shelf and plywood back. A perfect gift-sized build.")
    difficulty = "Beginner"
    estimated_time_hours = 3.0
    params = [
        ParamSpec("width_in", "Width", "number", 18,
                  min_val=14, max_val=26, step=1, unit="in",
                  help="18-20 in. suits most beds."),
        ParamSpec("height_in", "Height", "number", 24,
                  min_val=20, max_val=32, step=1, unit="in",
                  help="Match your mattress top: usually 24-28 in."),
        ParamSpec("include_shelf", "Mid shelf (open cubby)", "boolean", True),
        ParamSpec("include_back", "Plywood back panel", "boolean", True),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        H = p["height_in"]
        shelf = p["include_shelf"]
        back = p["include_back"]

        BOARD_T = 0.75
        DEPTH = 11.25
        inner_w = W - 2 * BOARD_T

        b = Build()

        # --- Cuts ---
        b.cuts.append(Cut("Side panel", "1x12", H, qty=2,
                          notes="Full height."))
        horiz = 2 + (1 if shelf else 0)
        b.cuts.append(Cut("Top / bottom" + (" / shelf" if shelf else ""),
                          "1x12", inner_w, qty=horiz,
                          notes=f"All {horiz} pieces identical length."))

        # --- Back panel ---
        if back:
            b.panels.append(PanelCut("Back panel", thickness_in=0.5,
                                     length_in=H, width_in=W, qty=1,
                                     notes="1/2\" plywood, squares the cabinet up."))

        # --- Hardware ---
        screws = horiz * 12
        if back:
            screws += int(2 * (W + H) / 6) + 4
        b.hardware.append(HardwareNeed("fastener.screws.wood.1.25in.1lb", screws,
                                       notes="1-1/4 in. wood screws"))
        b.hardware.append(HardwareNeed("finish.woodglue.16oz", 1))
        b.hardware.append(HardwareNeed("finish.sandpaper.assorted", 1))

        # --- 3D preview ---
        b.parts_3d.append(Part3D("Left side", 0, 0, 0, BOARD_T, DEPTH, H, "#c69c6d"))
        b.parts_3d.append(Part3D("Right side", W - BOARD_T, 0, 0, BOARD_T, DEPTH, H, "#c69c6d"))
        b.parts_3d.append(Part3D("Bottom", BOARD_T, 0, 2, inner_w, DEPTH, BOARD_T, "#d6b48a"))
        b.parts_3d.append(Part3D("Top", BOARD_T, 0, H - BOARD_T, inner_w, DEPTH, BOARD_T, "#d6b48a"))
        if shelf:
            b.parts_3d.append(Part3D("Shelf", BOARD_T, 0, H * 0.55,
                                     inner_w, DEPTH, BOARD_T, "#d6b48a"))
        if back:
            b.parts_3d.append(Part3D("Back panel", 0, DEPTH, 0, W, 0.5, H, "#a87b4f"))

        b.notes.append("Predrill all screw holes with a 1/8\" bit — pine splits easily near ends.")
        b.notes.append("A coat of stain + poly turns this from 'shop project' into furniture.")
        b.assembly_hints = {
            "width_in": W, "height_in": H,
            "include_shelf": shelf, "include_back": back,
        }
        return b
