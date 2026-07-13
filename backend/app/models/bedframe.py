"""Platform bed frame parametric model.

A sturdy platform bed: 2x6 side/head/foot rails on 4x4 legs, a 2x6
center beam with its own leg for wider sizes, and 1x4 slats — no box
spring needed.

Common mattress sizes (width x length, inches):
  Twin 38x75 · Full 54x75 · Queen 60x80 · King 76x80

Geometry: X = width, Y = length (head->foot), Z = height.
"""
import math
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class BedFrameModel(ProjectModel):
    id = "bedframe"
    name = "Platform Bed Frame"
    description = ("A solid platform bed from 2x6 rails, 4x4 legs, and 1x4 "
                   "slats. No box spring needed. Defaults fit a queen.")
    difficulty = "Intermediate"
    estimated_time_hours = 6.0
    params = [
        ParamSpec("mattress_width_in", "Mattress width", "number", 60,
                  min_val=38, max_val=76, step=1, unit="in",
                  help="Twin 38 · Full 54 · Queen 60 · King 76."),
        ParamSpec("mattress_length_in", "Mattress length", "number", 80,
                  min_val=74, max_val=84, step=1, unit="in",
                  help="Twin/Full 75 · Queen/King 80."),
        ParamSpec("platform_height_in", "Platform height (top of slats)", "number", 14,
                  min_val=10, max_val=18, step=1, unit="in",
                  help="14 in. + a 10-12 in. mattress puts the sleep surface ~ chair height."),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        MW = p["mattress_width_in"]
        ML = p["mattress_length_in"]
        PH = p["platform_height_in"]

        RAIL_T = 1.5   # 2x6 actual
        RAIL_W = 5.5
        LEG = 3.5      # 4x4 actual
        SLAT_T = 0.75  # 1x4 actual
        SLAT_W = 3.5
        CLEAR = 1.0    # clearance around mattress

        # Outer frame dimensions (mattress + clearance sits inside the rails)
        W = MW + 2 * CLEAR + 2 * RAIL_T
        L = ML + 2 * CLEAR + 2 * RAIL_T
        leg_h = PH - SLAT_T          # slats sit on top of cleats at leg top
        rail_z = leg_h - RAIL_W      # rails hang so their top is flush with leg top

        b = Build()

        # --- Cuts ---
        b.cuts.append(Cut("Side rail", "2x6", L, qty=2,
                          notes="Full length of the frame."))
        b.cuts.append(Cut("Head/foot rail", "2x6", W - 2 * RAIL_T, qty=2,
                          notes="Fits between the side rails."))
        b.cuts.append(Cut("Leg", "4x4", leg_h, qty=4,
                          notes="Pressure-treated is fine; it's hidden."))
        # Center beam + center leg for queen and wider
        center = MW >= 54
        if center:
            b.cuts.append(Cut("Center beam", "2x6", L - 2 * RAIL_T, qty=1,
                              notes="Runs head-to-foot down the middle — stops slat sag."))
            b.cuts.append(Cut("Center leg", "4x4", rail_z, qty=1,
                              notes="Supports the center beam at midspan."))
        # Slat cleats: 1x4 ripped... keep simple: use 1x4 full width as cleat
        b.cuts.append(Cut("Slat cleat", "1x4", L - 2 * RAIL_T, qty=2,
                          notes="Screwed inside each side rail; the slats rest on these."))
        # Slats at ~3" spacing
        n_slats = max(8, int(math.ceil(ML / (SLAT_W + 2.5))))
        b.cuts.append(Cut("Slat", "1x4", W - 2 * RAIL_T - 0.5, qty=n_slats,
                          notes=f"{n_slats} slats, spaced ~2-3 in. apart."))

        # --- Hardware ---
        b.hardware.append(HardwareNeed("fastener.screws.deck.3in.5lb", 1,
                                       notes="Rails to legs: 4 screws per corner + glue."))
        slat_screws = n_slats * 2 + 40
        b.hardware.append(HardwareNeed("fastener.screws.wood.2in.1lb",
                                       max(1, -(-slat_screws // 125)),
                                       notes="Cleats and slats."))
        b.hardware.append(HardwareNeed("finish.woodglue.16oz", 1))
        b.hardware.append(HardwareNeed("finish.sandpaper.assorted", 1))

        # --- 3D preview ---
        # Legs
        for (x, y) in [(0, 0), (W - LEG, 0), (0, L - LEG), (W - LEG, L - LEG)]:
            b.parts_3d.append(Part3D("Leg", x, y, 0, LEG, LEG, leg_h, "#8b5a2b"))
        # Rails
        b.parts_3d.append(Part3D("Side rail L", 0, 0, rail_z, RAIL_T, L, RAIL_W, "#c69c6d"))
        b.parts_3d.append(Part3D("Side rail R", W - RAIL_T, 0, rail_z, RAIL_T, L, RAIL_W, "#c69c6d"))
        b.parts_3d.append(Part3D("Head rail", RAIL_T, 0, rail_z, W - 2 * RAIL_T, RAIL_T, RAIL_W, "#c69c6d"))
        b.parts_3d.append(Part3D("Foot rail", RAIL_T, L - RAIL_T, rail_z, W - 2 * RAIL_T, RAIL_T, RAIL_W, "#c69c6d"))
        if center:
            b.parts_3d.append(Part3D("Center beam", W / 2 - RAIL_T / 2, RAIL_T, rail_z,
                                     RAIL_T, L - 2 * RAIL_T, RAIL_W, "#a87b4f"))
            b.parts_3d.append(Part3D("Center leg", W / 2 - LEG / 2, L / 2 - LEG / 2, 0,
                                     LEG, LEG, rail_z, "#8b5a2b"))
        # Slats
        gap = (L - 2 * RAIL_T - n_slats * SLAT_W) / max(1, n_slats - 1)
        for i in range(n_slats):
            y = RAIL_T + i * (SLAT_W + gap)
            b.parts_3d.append(Part3D(f"Slat {i+1}", RAIL_T + 0.25, y, leg_h,
                                     W - 2 * RAIL_T - 0.5, SLAT_W, SLAT_T, "#d6b48a"))

        b.notes.append("Glue + screw every rail-to-leg joint; the glue does most of the work.")
        b.notes.append("Screw down every third slat and the two end slats — the rest can float.")
        if center:
            b.notes.append("Queen and wider need the center beam — without it, slats sag within a year.")
        b.assembly_hints = {
            "mattress_width_in": MW, "mattress_length_in": ML,
            "frame_width_in": round(W, 1), "frame_length_in": round(L, 1),
            "platform_height_in": PH, "n_slats": n_slats,
            "center_beam": center, "leg_height_in": round(leg_h, 2),
        }
        return b
