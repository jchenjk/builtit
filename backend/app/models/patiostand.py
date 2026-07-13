"""Tiered patio plant stand parametric model.

A ladder-style outdoor stand: two 2x4 side frames connected by slatted
1x4 shelves that step back tier by tier. Great for potted plants, boots,
or firewood on a covered patio.

Geometry: X = width, Y = depth (front->back), Z = height.
Each tier is one shelf; tier 1 is lowest and at the front, higher tiers
step up and back like stadium seating.
"""
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class PatioStandModel(ProjectModel):
    id = "patio_stand"
    name = "Patio Plant Stand"
    description = ("A tiered, ladder-style outdoor stand with slatted shelves — "
                   "for plants, boots, or anything that likes a patio.")
    difficulty = "Beginner"
    estimated_time_hours = 3.5
    params = [
        ParamSpec("width_in", "Width", "number", 36,
                  min_val=24, max_val=60, step=2, unit="in"),
        ParamSpec("tiers", "Number of tiers", "integer", 3,
                  min_val=2, max_val=4),
        ParamSpec("tier_depth_in", "Shelf depth per tier", "number", 11,
                  min_val=8, max_val=14, step=1, unit="in"),
        ParamSpec("tier_rise_in", "Height step between tiers", "number", 10,
                  min_val=8, max_val=14, step=1, unit="in"),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        TIERS = p["tiers"]
        TD = p["tier_depth_in"]
        RISE = p["tier_rise_in"]

        F_T = 1.5      # 2x4 actual thickness
        F_W = 3.5      # 2x4 actual width
        SLAT_W = 3.5   # 1x4 actual width
        SLAT_T = 0.75
        GAP = 0.5      # gap between slats (drainage)

        total_depth = TIERS * TD
        total_height = TIERS * RISE + F_T

        b = Build()

        # --- Cuts ---
        # Side frames: each side is a stepped "staircase" made from:
        #   1 back post (full height), 1 front post (1 tier tall),
        #   and one horizontal bearer per tier.
        b.cuts.append(Cut("Back post", "2x4", total_height, qty=2,
                          notes="Full height, one per side."))
        b.cuts.append(Cut("Front post", "2x4", RISE, qty=2,
                          notes="Supports the lowest tier at the front."))
        # Intermediate posts under each higher tier's front edge
        if TIERS > 1:
            for t in range(2, TIERS + 1):
                b.cuts.append(Cut(f"Tier {t} post", "2x4", RISE * t, qty=2,
                                  notes="Supports the front edge of this tier."))
        b.cuts.append(Cut("Tier bearer (side)", "2x4", TD, qty=TIERS * 2,
                          notes="Horizontal supports each shelf sits on — one per side per tier."))
        # Cross rails tying the two sides together (front + back per tier)
        b.cuts.append(Cut("Cross rail", "2x4", W - 2 * F_T, qty=TIERS * 2,
                          notes="Connects the two side frames at each tier, front and back."))
        # Shelf slats: run the width; count per tier depends on depth
        n_slats = max(2, int((TD + GAP) // (SLAT_W + GAP)))
        b.cuts.append(Cut("Shelf slat", "1x4", W, qty=TIERS * n_slats,
                          notes=f"{n_slats} slats per tier with ~1/2 in. drainage gaps."))

        # --- Hardware ---
        # 2 deck screws per slat end + 4 per frame joint
        joints = TIERS * 8 + 8
        slat_screws = TIERS * n_slats * 4
        b.hardware.append(HardwareNeed("fastener.screws.deck.3in.5lb", 1,
                                       notes="Exterior deck screws for the 2x4 frame."))
        b.hardware.append(HardwareNeed("fastener.screws.wood.2in.1lb",
                                       max(1, -(-slat_screws // 125)),
                                       notes="For fastening slats to bearers."))
        b.hardware.append(HardwareNeed("finish.sandpaper.assorted", 1))

        # --- 3D preview ---
        for side_x in (0, W - F_T):
            # Back post
            b.parts_3d.append(Part3D("Back post", side_x, total_depth - F_W, 0,
                                     F_T, F_W, total_height, "#8b5a2b"))
            # Posts under each tier front edge
            for t in range(1, TIERS + 1):
                y = total_depth - t * TD
                b.parts_3d.append(Part3D(f"Tier {t} post", side_x, y, 0,
                                         F_T, F_W, RISE * t, "#8b5a2b"))
                # Bearer
                b.parts_3d.append(Part3D(f"Tier {t} bearer", side_x, y, RISE * t - F_T + F_T,
                                         F_T, TD, F_T, "#a87b4f"))
        # Slats per tier
        for t in range(1, TIERS + 1):
            y0 = total_depth - t * TD
            z = RISE * t + F_T
            for s in range(n_slats):
                sy = y0 + s * (SLAT_W + GAP)
                if sy + SLAT_W > y0 + TD + 0.1:
                    break
                b.parts_3d.append(Part3D(f"T{t} slat {s+1}", 0, sy, z,
                                         W, SLAT_W, SLAT_T, "#d6b48a"))

        b.notes.append("Use exterior screws and seal all surfaces — this build lives outside.")
        b.notes.append("Pine works on a covered patio; use pressure-treated or cedar for full weather exposure.")
        b.assembly_hints = {
            "width_in": W, "tiers": TIERS, "tier_depth_in": TD,
            "tier_rise_in": RISE, "n_slats": n_slats,
            "total_height_in": total_height,
        }
        return b
