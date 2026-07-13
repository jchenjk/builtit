"""Wine rack parametric model.

A horizontal-bottle wine rack from 1x12 pine: two sides, a row of
shelves, and 1x4 rails across the front and back of each row that keep
bottles from rolling off. Bottles lie neck-forward between the rails.

Geometry: X = width, Y = depth (11.25"), Z = height.
Each row is 4.5" of clear height — enough for a standard 3-3.2" dia bottle.
"""
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel

ROW_H = 4.75     # clear height per bottle row
BOARD_T = 0.75
DEPTH = 11.25
BOTTLE_PITCH = 3.6  # width per bottle


class WineRackModel(ProjectModel):
    id = "winerack"
    name = "Wine Rack"
    description = ("A horizontal-bottle wine rack from 1x12 pine with rail "
                   "fronts. Sized by rows — each bottle rests on its side, "
                   "cork wet, like a proper cellar.")
    difficulty = "Beginner"
    estimated_time_hours = 3.0
    params = [
        ParamSpec("width_in", "Width", "number", 24,
                  min_val=16, max_val=40, step=1, unit="in",
                  help="Each ~3.6 in. of inside width holds one bottle per row."),
        ParamSpec("rows", "Bottle rows", "integer", 4, min_val=2, max_val=8),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        ROWS = p["rows"]

        inner_w = W - 2 * BOARD_T
        bottles_per_row = int(inner_w // BOTTLE_PITCH)
        H = ROWS * (ROW_H + BOARD_T) + BOARD_T

        b = Build()

        # --- Cuts ---
        b.cuts.append(Cut("Side panel", "1x12", H, qty=2))
        b.cuts.append(Cut("Shelf", "1x12", inner_w, qty=ROWS + 1,
                          notes="One under each row plus the top."))
        b.cuts.append(Cut("Bottle rail", "1x4", inner_w, qty=ROWS * 2,
                          notes="Front + back of each row; stops bottles rolling."))

        # --- Hardware ---
        screws = (ROWS + 1) * 12 + ROWS * 8
        b.hardware.append(HardwareNeed("fastener.screws.wood.1.25in.1lb", screws,
                                       notes="1-1/4 in. wood screws"))
        b.hardware.append(HardwareNeed("finish.woodglue.16oz", 1))
        b.hardware.append(HardwareNeed("finish.sandpaper.assorted", 1))

        # --- 3D preview ---
        b.parts_3d.append(Part3D("Left side", 0, 0, 0, BOARD_T, DEPTH, H, "#c69c6d"))
        b.parts_3d.append(Part3D("Right side", W - BOARD_T, 0, 0, BOARD_T, DEPTH, H, "#c69c6d"))
        for r in range(ROWS + 1):
            z = r * (ROW_H + BOARD_T)
            b.parts_3d.append(Part3D(f"Shelf {r+1}", BOARD_T, 0, z,
                                     inner_w, DEPTH, BOARD_T, "#d6b48a"))
        # Rails (front + back of each row, sitting on the shelf below)
        for r in range(ROWS):
            z = r * (ROW_H + BOARD_T) + BOARD_T
            b.parts_3d.append(Part3D(f"Row {r+1} front rail", BOARD_T, 0.25, z,
                                     inner_w, 0.75, 3.5, "#a87b4f"))
            b.parts_3d.append(Part3D(f"Row {r+1} back rail", BOARD_T, DEPTH - 1.0, z,
                                     inner_w, 0.75, 3.5, "#a87b4f"))
        # A few "bottles" so the preview reads instantly
        for r in range(min(ROWS, 3)):
            z = r * (ROW_H + BOARD_T) + BOARD_T + 0.6
            for i in range(min(bottles_per_row, 5)):
                x = BOARD_T + 0.5 + i * BOTTLE_PITCH
                b.parts_3d.append(Part3D("Bottle", x, 1.2, z,
                                         3.0, DEPTH - 2.4, 3.0, "#5b7553"))

        b.notes.append(f"This size holds ~{bottles_per_row * ROWS} bottles "
                       f"({bottles_per_row} per row × {ROWS} rows).")
        b.notes.append("Store bottles label-up with the cork end slightly low so corks stay wet.")
        b.assembly_hints = {
            "width_in": W, "rows": ROWS, "height_in": round(H, 1),
            "bottles_per_row": bottles_per_row,
            "capacity": bottles_per_row * ROWS,
        }
        return b
