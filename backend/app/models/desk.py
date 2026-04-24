"""Simple desk parametric model.

Tabletop from 3/4" plywood with 1x4 pine edge banding.
Four 4x4 (or 2x4 doubled) legs, joined by 1x4 aprons.
"""
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class DeskModel(ProjectModel):
    id = "desk"
    name = "Simple Desk"
    description = ("A clean, modern desk: plywood top with pine edge banding "
                   "on a four-leg apron frame.")
    difficulty = "Beginner"
    estimated_time_hours = 6.0
    params = [
        ParamSpec("width_in", "Width", "number", 48,
                  min_val=36, max_val=72, step=1, unit="in"),
        ParamSpec("depth_in", "Depth", "number", 24,
                  min_val=18, max_val=30, step=1, unit="in"),
        ParamSpec("height_in", "Height", "number", 30,
                  min_val=28, max_val=32, step=1, unit="in",
                  help="Standard desk height is 29-30 inches."),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        D = p["depth_in"]
        H = p["height_in"]

        TOP_T = 0.75    # 3/4" plywood top
        EDGE_T = 0.75   # 1x4 edge band
        EDGE_W = 3.5
        LEG = 3.5       # 4x4 leg actual
        APRON_T = 0.75
        APRON_W = 3.5

        b = Build()
        leg_h = H - TOP_T

        # --- Cuts ---
        b.cuts.append(Cut("Leg", "4x4", leg_h, qty=4,
                          notes="Cut all four legs to identical length."))
        # Aprons: front/back run the full inner width between legs.
        # Inset legs by edge band thickness so aprons are length = W - 2*LEG
        apron_long = W - 2 * LEG
        apron_short = D - 2 * LEG
        b.cuts.append(Cut("Long apron (front/back)", "1x4", apron_long, qty=2))
        b.cuts.append(Cut("Short apron (sides)", "1x4", apron_short, qty=2))
        # Edge banding (4 strips around the top)
        b.cuts.append(Cut("Edge band, long", "1x4", W, qty=2,
                          notes="Front and back edge of the tabletop."))
        b.cuts.append(Cut("Edge band, short", "1x4", D, qty=2,
                          notes="Left and right edges. Mitered or butt joints — your call."))

        # --- Top panel ---
        b.panels.append(PanelCut("Tabletop", thickness_in=TOP_T,
                                 length_in=W, width_in=D, qty=1,
                                 notes="Cut from a 4x8 sheet of 3/4\" plywood."))

        # --- Hardware ---
        # 8 screws per leg-to-apron joint x 4 legs x 2 aprons = ~32 long screws
        # plus screws to attach top: ~12 around perimeter
        b.hardware.append(HardwareNeed("fastener.screws.deck.3in.5lb", 32,
                                       notes="3 in. screws for leg-to-apron joints"))
        b.hardware.append(HardwareNeed("fastener.screws.wood.2in.1lb", 24,
                                       notes="2 in. screws for top + edge bands"))
        b.hardware.append(HardwareNeed("finish.woodglue.16oz", 1))
        b.hardware.append(HardwareNeed("finish.sandpaper.assorted", 1))
        b.hardware.append(HardwareNeed("finish.polyurethane.qt", 1,
                                       notes="To seal the desktop"))

        # --- 3D preview ---
        # Legs at four corners
        for (lx, ly) in [(0, 0), (W - LEG, 0), (0, D - LEG), (W - LEG, D - LEG)]:
            b.parts_3d.append(Part3D("Leg", lx, ly, 0, LEG, LEG, leg_h, "#8b5a2b"))
        # Long aprons
        b.parts_3d.append(Part3D("Front apron", LEG, 0, leg_h - APRON_W,
                                 apron_long, APRON_T, APRON_W, "#a87b4f"))
        b.parts_3d.append(Part3D("Back apron", LEG, D - APRON_T, leg_h - APRON_W,
                                 apron_long, APRON_T, APRON_W, "#a87b4f"))
        # Short aprons
        b.parts_3d.append(Part3D("Left apron", 0, LEG, leg_h - APRON_W,
                                 APRON_T, apron_short, APRON_W, "#a87b4f"))
        b.parts_3d.append(Part3D("Right apron", W - APRON_T, LEG, leg_h - APRON_W,
                                 APRON_T, apron_short, APRON_W, "#a87b4f"))
        # Tabletop
        b.parts_3d.append(Part3D("Tabletop", 0, 0, leg_h, W, D, TOP_T, "#d6b48a"))

        b.notes.append(
            "If you don't have access to 4x4 lumber, two 2x4s glued and screwed together make a great leg."
        )
        b.assembly_hints = {"width_in": W, "depth_in": D, "height_in": H}
        return b
