"""Bookshelf parametric model.

Built from 1x12 pine: two side panels, a top, a bottom, and N adjustable
shelves. Backed with 1/2" plywood, fastened with 1-1/4" wood screws.

Geometry convention (right-handed, inches):
  X = width (left-right)
  Y = depth (front-back)  -> bookshelf depth ~ 11.25"
  Z = height (up)
"""
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class BookshelfModel(ProjectModel):
    id = "bookshelf"
    name = "Bookshelf"
    description = ("A simple, sturdy bookshelf built from 1x12 pine boards "
                   "and a plywood back. Great first project.")
    difficulty = "Beginner"
    estimated_time_hours = 4.0
    params = [
        ParamSpec("width_in", "Width", "number", 30,
                  min_val=18, max_val=48, step=1, unit="in",
                  help="Outside width of the bookshelf."),
        ParamSpec("height_in", "Height", "number", 60,
                  min_val=24, max_val=84, step=1, unit="in"),
        ParamSpec("shelves", "Number of shelves (between top and bottom)",
                  "integer", 3, min_val=1, max_val=6),
        ParamSpec("include_back", "Plywood back panel", "boolean", True),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        H = p["height_in"]
        shelves = p["shelves"]
        back = p["include_back"]

        # 1x12 actual: 0.75 x 11.25
        BOARD_T = 0.75
        DEPTH = 11.25

        # Side panels run full height. Top/bottom/shelves sit BETWEEN sides.
        inner_w = W - 2 * BOARD_T

        b = Build()

        # --- Cuts ---
        b.cuts.append(Cut("Side panel", "1x12", H, qty=2,
                          notes="Full height. These hold everything together."))
        # top + bottom + interior shelves
        total_shelves = 2 + shelves
        b.cuts.append(Cut("Top / bottom / shelf", "1x12", inner_w, qty=total_shelves,
                          notes=f"Cut all {total_shelves} pieces to identical length."))

        # --- Panels (back) ---
        if back:
            b.panels.append(PanelCut("Back panel", thickness_in=0.5,
                                     length_in=H, width_in=W,
                                     qty=1,
                                     notes="Cut from a 4x8 sheet of 1/2\" plywood."))

        # --- Hardware ---
        # ~6 screws per joint, 2 joints per shelf (left + right side) = 12/shelf
        screws = total_shelves * 12
        if back:
            # back panel attached every ~6"
            perimeter = 2 * (W + H)
            screws += int(perimeter / 6) + 4
        b.hardware.append(HardwareNeed("fastener.screws.wood.1.25in.1lb", screws,
                                       notes="1-1/4 in. wood screws"))
        b.hardware.append(HardwareNeed("finish.woodglue.16oz", 1))
        b.hardware.append(HardwareNeed("finish.sandpaper.assorted", 1))

        # --- 3D preview ---
        # Sides
        b.parts_3d.append(Part3D("Left side", 0, 0, 0, BOARD_T, DEPTH, H, "#c69c6d"))
        b.parts_3d.append(Part3D("Right side", W - BOARD_T, 0, 0, BOARD_T, DEPTH, H, "#c69c6d"))
        # Bottom
        b.parts_3d.append(Part3D("Bottom", BOARD_T, 0, 0, inner_w, DEPTH, BOARD_T, "#d6b48a"))
        # Top
        b.parts_3d.append(Part3D("Top", BOARD_T, 0, H - BOARD_T, inner_w, DEPTH, BOARD_T, "#d6b48a"))
        # Interior shelves equally spaced
        gaps = shelves + 1
        usable_h = H - 2 * BOARD_T
        for i in range(1, gaps):
            z = BOARD_T + (usable_h * i / gaps) - BOARD_T / 2
            b.parts_3d.append(Part3D(f"Shelf {i}", BOARD_T, 0, z,
                                     inner_w, DEPTH, BOARD_T, "#d6b48a"))
        if back:
            b.parts_3d.append(Part3D("Back panel", 0, DEPTH, 0,
                                     W, 0.5, H, "#a87b4f"))

        b.notes.append(
            "Predrill all screw holes with a 1/8\" bit to prevent the pine from splitting."
        )
        b.assembly_hints = {
            "shelves": shelves,
            "include_back": back,
            "width_in": W,
            "height_in": H,
        }
        return b
