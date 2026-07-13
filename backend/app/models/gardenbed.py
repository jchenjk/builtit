"""Raised garden bed parametric model.

Stacked pressure-treated 2x6 courses with 4x4 corner posts inside the
box. One afternoon, decades of tomatoes.

Geometry: X = length, Y = width, Z = height (courses of 5.5" each).
"""
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class GardenBedModel(ProjectModel):
    id = "gardenbed"
    name = "Raised Garden Bed"
    description = ("A raised planting bed from pressure-treated 2x6 courses "
                   "with 4x4 corner posts. The easiest build in the catalog.")
    difficulty = "Beginner"
    estimated_time_hours = 2.0
    params = [
        ParamSpec("length_in", "Length", "number", 96,
                  min_val=48, max_val=144, step=12, unit="in"),
        ParamSpec("width_in", "Width", "number", 48,
                  min_val=24, max_val=48, step=6, unit="in",
                  help="48 in. max lets you reach the middle from either side."),
        ParamSpec("courses", "Board courses (height)", "integer", 2,
                  min_val=1, max_val=3,
                  help="Each course adds 5-1/2 in. of soil depth."),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        L = p["length_in"]
        W = p["width_in"]
        C = p["courses"]

        T = 1.5     # 2x6 actual
        BW = 5.5
        POST = 3.5
        H = C * BW

        b = Build()

        # --- Cuts ---
        b.cuts.append(Cut("Long side board", "2x6pt", L, qty=2 * C,
                          notes="Pressure-treated — modern PT is safe for vegetable beds."))
        b.cuts.append(Cut("Short side board", "2x6pt", W - 2 * T, qty=2 * C,
                          notes="Fits between the long boards."))
        b.cuts.append(Cut("Corner post", "4x4", H, qty=4,
                          notes="Inside each corner; every course screws into it."))
        if L >= 96:
            b.cuts.append(Cut("Mid-span stake", "4x4", H + 6, qty=2,
                              notes="Halfway down each long side, driven into the soil — "
                                    "stops the sides bowing out."))

        # --- Hardware ---
        b.hardware.append(HardwareNeed("fastener.screws.deck.3in.5lb", 1,
                                       notes="Exterior deck screws, 3 per board end into the post."))

        # --- 3D preview ---
        for c in range(C):
            z = c * BW
            b.parts_3d.append(Part3D(f"Long side A c{c+1}", 0, 0, z, L, T, BW, "#7a6248"))
            b.parts_3d.append(Part3D(f"Long side B c{c+1}", 0, W - T, z, L, T, BW, "#7a6248"))
            b.parts_3d.append(Part3D(f"Short side A c{c+1}", 0, T, z, T, W - 2 * T, BW, "#84674b"))
            b.parts_3d.append(Part3D(f"Short side B c{c+1}", L - T, T, z, T, W - 2 * T, BW, "#84674b"))
        for (x, y) in [(T, T), (L - T - POST, T), (T, W - T - POST), (L - T - POST, W - T - POST)]:
            b.parts_3d.append(Part3D("Corner post", x, y, 0, POST, POST, H, "#6b4f3a"))
        # Soil fill for the preview
        b.parts_3d.append(Part3D("Soil", T, T, max(0, H - 2),
                                 L - 2 * T, W - 2 * T, 1.5, "#4a3728"))

        soil_cuft = (L * W * H) / 1728 * 0.9
        b.notes.append(f"You'll need roughly {soil_cuft:.0f} cu ft of soil "
                       f"(~{soil_cuft / 27:.1f} cu yd). Bulk delivery beats bags past 1 yd.")
        b.notes.append("Line the bottom with cardboard to kill grass — it composts in place.")
        b.assembly_hints = {
            "length_in": L, "width_in": W, "courses": C,
            "height_in": H, "soil_cuft": round(soil_cuft, 1),
        }
        return b
