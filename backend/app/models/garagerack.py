"""Heavy-duty garage/yard storage rack parametric model.

The classic 2x4 + plywood utility shelf: six posts (four corners + two
mid-span), 2x4 rail frames at each shelf level, and 3/4" plywood decks.
Holds totes, paint, power tools — roughly 300 lb per shelf when built
as drawn.

Geometry: X = width, Y = depth, Z = height.
"""
import math
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class GarageRackModel(ProjectModel):
    id = "garagerack"
    name = "Garage Storage Rack"
    description = ("A heavy-duty 2x4 + plywood shelving unit for the garage "
                   "or yard shed. Cheap, fast, and holds a small car's worth "
                   "of totes.")
    difficulty = "Beginner"
    estimated_time_hours = 4.0
    params = [
        ParamSpec("width_in", "Width", "number", 72,
                  min_val=48, max_val=96, step=4, unit="in"),
        ParamSpec("depth_in", "Depth", "number", 20,
                  min_val=16, max_val=24, step=2, unit="in",
                  help="20-24 in. fits standard storage totes."),
        ParamSpec("height_in", "Height", "number", 72,
                  min_val=48, max_val=84, step=4, unit="in"),
        ParamSpec("shelves", "Number of shelves", "integer", 4,
                  min_val=3, max_val=5),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        D = p["depth_in"]
        H = p["height_in"]
        SHELVES = p["shelves"]

        T = 1.5   # 2x4 actual
        FW = 3.5

        b = Build()

        # --- Cuts ---
        # 6 posts: 4 corners + 2 mid-width (front/back) for long spans
        n_posts = 6 if W > 60 else 4
        b.cuts.append(Cut("Post", "2x4", H, qty=n_posts,
                          notes=f"{n_posts} posts — corners"
                                + (" plus mid-span front/back." if n_posts == 6 else ".")))
        # Each shelf level: 2 long rails + cross supports every ~16"
        n_cross = max(2, int(math.ceil(W / 16)) + 1)
        b.cuts.append(Cut("Shelf rail (long)", "2x4", W, qty=SHELVES * 2,
                          notes="Front and back of each shelf frame."))
        b.cuts.append(Cut("Shelf cross support", "2x4", D - 2 * T, qty=SHELVES * n_cross,
                          notes=f"{n_cross} per shelf, every ~16 in."))
        # Plywood decks
        b.panels.append(PanelCut("Shelf deck", thickness_in=0.75,
                                 length_in=W, width_in=D, qty=SHELVES,
                                 notes="3/4\" plywood. Rip a 4x8 sheet into strips."))

        # --- Hardware ---
        b.hardware.append(HardwareNeed("fastener.screws.deck.3in.5lb", 1,
                                       notes="Frame joints: 2-3 screws each."))
        b.hardware.append(HardwareNeed("fastener.screws.wood.2in.1lb", 1,
                                       notes="Decks to frames."))

        # --- 3D preview ---
        post_xs = [0, W - T] if n_posts == 4 else [0, W / 2 - T / 2, W - T]
        for x in post_xs:
            for y in (0, D - FW):
                b.parts_3d.append(Part3D("Post", x, y, 0, T, FW, H, "#8b5a2b"))
        for s in range(SHELVES):
            z = 6 + s * (H - 10) / max(1, SHELVES - 1)
            b.parts_3d.append(Part3D(f"Shelf {s+1} front rail", 0, 0, z, W, T, FW, "#a87b4f"))
            b.parts_3d.append(Part3D(f"Shelf {s+1} back rail", 0, D - T, z, W, T, FW, "#a87b4f"))
            b.parts_3d.append(Part3D(f"Shelf {s+1} deck", 0, 0, z + FW,
                                     W, D, 0.75, "#d6b48a"))

        b.notes.append("Screw the back posts into wall studs if the rack lives against a wall — "
                       "a loaded rack is heavy and must not tip.")
        b.notes.append("Put the heaviest stuff on the bottom shelf.")
        b.assembly_hints = {
            "width_in": W, "depth_in": D, "height_in": H,
            "shelves": SHELVES, "n_posts": n_posts, "n_cross": n_cross,
        }
        return b
