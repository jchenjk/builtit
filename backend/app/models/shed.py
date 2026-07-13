"""Storage shed parametric model.

A simple gable-roof shed on a pressure-treated 4x4 skid foundation.
Stick-framed walls (2x4 @ 16" o.c.), OSB sheathing, asphalt-shingle roof.

This is a beginner-friendly *small* shed (e.g. 8x6 to 10x8). Building codes
vary by jurisdiction — many areas allow sheds under ~120 sq ft without a
permit, but always check locally.
"""
import math
from .base import Build, Cut, PanelCut, HardwareNeed, Part3D, ParamSpec, ProjectModel


class ShedModel(ProjectModel):
    id = "shed"
    name = "Storage Shed"
    description = ("A small gable-roof storage shed on a 4x4 skid foundation. "
                   "Stick-framed walls, OSB sheathing, asphalt-shingle roof.")
    difficulty = "Intermediate"
    estimated_time_hours = 24.0
    params = [
        ParamSpec("width_in", "Width", "number", 96,
                  min_val=72, max_val=144, step=12, unit="in",
                  help="Wall length facing forward."),
        ParamSpec("depth_in", "Depth", "number", 72,
                  min_val=60, max_val=120, step=12, unit="in"),
        ParamSpec("wall_height_in", "Wall height", "number", 84,
                  min_val=72, max_val=96, step=6, unit="in"),
        ParamSpec("roof_pitch", "Roof pitch (rise per 12 in. run)", "number", 4,
                  min_val=3, max_val=8, step=1, unit="/12",
                  help="A 4/12 pitch is gentle and easy to walk on."),
        ParamSpec("door_width_in", "Door width", "number", 36,
                  min_val=30, max_val=48, step=2, unit="in"),
    ]

    @classmethod
    def generate(cls, params: dict) -> Build:
        p = cls.coerce(params)
        W = p["width_in"]
        D = p["depth_in"]
        WH = p["wall_height_in"]
        PITCH = p["roof_pitch"]
        DOOR_W = p["door_width_in"]

        STUD_T = 1.5    # 2x4 actual
        STUD_W = 3.5
        SHEATH_T = 0.4375
        STUD_SPACING = 16  # inches o.c.

        b = Build()

        # --- Foundation (skids) ---
        # Two 4x4 skids running along the depth, plus two short ones for ends
        b.cuts.append(Cut("Foundation skid", "4x4", D, qty=2,
                          notes="Pressure-treated. These sit on gravel/blocks."))

        # --- Floor frame (joists) ---
        # 2x6 joists @ 16" o.c. across width
        n_joists = max(2, int(math.ceil(W / STUD_SPACING)) + 1)
        b.cuts.append(Cut("Floor joist", "2x6", D, qty=n_joists,
                          notes=f"Spaced 16 in. on center. {n_joists} total."))
        b.cuts.append(Cut("Floor rim joist", "2x6", W, qty=2,
                          notes="Front and back of floor frame."))

        # Floor decking: 3/4" plywood (count sheets needed for W*D area)
        floor_sheets = math.ceil((W * D) / (48 * 96))
        b.panels.append(PanelCut("Floor decking", thickness_in=0.75,
                                 length_in=96, width_in=48, qty=floor_sheets,
                                 notes=f"3/4\" plywood. ~{floor_sheets} sheet(s) to cover the floor."))

        # --- Walls (stick framing) ---
        # Each wall: top + bottom plate + studs.
        # Front wall has a door rough opening.
        # 2x4 studs 'WH - 4.5" (top + bottom plate + extra plate)' tall
        stud_len = WH - 3 * STUD_T  # bottom plate + double top plate

        # Wall stud counts (excluding king/jack studs near openings, kept simple)
        def studs_for_length(L):
            return max(2, int(math.ceil(L / STUD_SPACING)) + 1)

        front_studs = studs_for_length(W) - studs_for_length(DOOR_W) + 4  # add jack/king/header
        back_studs = studs_for_length(W)
        side_studs = studs_for_length(D - 2 * STUD_T) * 2  # both side walls

        b.cuts.append(Cut("Wall stud", "2x4", stud_len,
                          qty=front_studs + back_studs + side_studs,
                          notes="All wall studs cut to the same length."))

        # Plates (top + bottom + double top for front/back)
        b.cuts.append(Cut("Wall top/bottom plate (front/back)", "2x4", W, qty=4,
                          notes="2 bottom + 2 top (double top plate stack later)."))
        b.cuts.append(Cut("Wall top/bottom plate (sides)", "2x4", D - 2 * STUD_T, qty=4))
        # Door header (simple single-2x4 header for a small shed)
        b.cuts.append(Cut("Door header", "2x4", DOOR_W + 2 * STUD_T, qty=1,
                          notes="Spans across the door rough opening."))

        # Sheathing for walls (perimeter * height)
        wall_area = 2 * (W + D) * WH / 144  # sqft
        # We don't subtract the door — extra is fine, you'll cut it out.
        wall_sheets = math.ceil(wall_area / 32)  # 4x8 = 32 sqft
        b.panels.append(PanelCut("Wall sheathing", thickness_in=SHEATH_T,
                                 length_in=96, width_in=48, qty=wall_sheets,
                                 notes=f"7/16\" OSB. ~{wall_sheets} sheet(s) for all four walls."))

        # --- Roof ---
        # Gable roof. Rafter length: hypotenuse of (W/2, W/2 * pitch/12)
        run = W / 2
        rise = run * PITCH / 12
        rafter_len = math.sqrt(run * run + rise * rise) + 6  # +6" overhang
        n_rafter_pairs = max(2, int(math.ceil(D / 24)) + 1)  # rafters at 24" o.c.
        b.cuts.append(Cut("Rafter", "2x4", rafter_len, qty=n_rafter_pairs * 2,
                          notes=f"Cut both ends to the roof angle (~{int(math.degrees(math.atan(PITCH/12)))}°). {n_rafter_pairs} pairs."))
        # Ridge board
        b.cuts.append(Cut("Ridge board", "2x6", D, qty=1,
                          notes="Spans the length of the roof at the peak."))

        # Roof sheathing area: 2 sloped planes of (rafter_len * D)
        roof_area_sqft = 2 * (rafter_len * D) / 144
        roof_sheets = math.ceil(roof_area_sqft / 32)
        b.panels.append(PanelCut("Roof sheathing", thickness_in=SHEATH_T,
                                 length_in=96, width_in=48, qty=roof_sheets))

        # Roofing felt + shingles
        b.hardware.append(HardwareNeed("roofing.felt.15lb.roll", 1))
        shingle_bundles = math.ceil(roof_area_sqft / 33.3)
        b.hardware.append(HardwareNeed("roofing.shingles.bundle", shingle_bundles,
                                       notes="Asphalt 3-tab shingles."))
        b.hardware.append(HardwareNeed("fastener.nails.roofing.1.25in.1lb", 1))

        # --- Door ---
        # Door = OSB on a 2x4 frame
        # Frame: 2 stiles (full height) + 2 rails (door width - 2*STUD_W)
        DOOR_H = WH - STUD_T - 2  # leave a gap above
        b.cuts.append(Cut("Door stile", "2x4", DOOR_H, qty=2))
        b.cuts.append(Cut("Door rail", "2x4", DOOR_W - 2 * STUD_W, qty=2))
        b.panels.append(PanelCut("Door panel", thickness_in=SHEATH_T,
                                 length_in=DOOR_H, width_in=DOOR_W, qty=1))
        b.hardware.append(HardwareNeed("hardware.hinge.3.5in.pair", 2,
                                       notes="2 pairs (4 hinges) for a sturdy shed door."))
        b.hardware.append(HardwareNeed("hardware.handle.barn", 1))

        # --- Fasteners overall ---
        # Framing nails for studs/plates/rafters
        b.hardware.append(HardwareNeed("fastener.nails.framing.16d.5lb", 2,
                                       notes="16d framing nails for stick framing."))
        # Deck screws for sheathing + plates
        b.hardware.append(HardwareNeed("fastener.screws.deck.3in.5lb", 1))
        # Wood screws for trim/door
        b.hardware.append(HardwareNeed("fastener.screws.wood.2in.1lb", 2))

        # --- 3D preview (schematic — axis-aligned boxes only) ---
        # Skids + floor
        b.parts_3d.append(Part3D("Skid L", W * 0.15, 0, 0, 3.5, D, 3.5, "#6b4f3a"))
        b.parts_3d.append(Part3D("Skid R", W * 0.85 - 3.5, 0, 0, 3.5, D, 3.5, "#6b4f3a"))
        FLOOR_Z = 3.5
        b.parts_3d.append(Part3D("Floor", 0, 0, FLOOR_Z, W, D, 1.5, "#a87b4f"))
        wall_z = FLOOR_Z + 1.5
        # Walls (as thin slabs); front wall gets a door opening (two segments + header)
        door_x0 = (W - DOOR_W) / 2
        door_h = WH - STUD_T - 2
        b.parts_3d.append(Part3D("Front wall L", 0, 0, wall_z, door_x0, STUD_T, WH, "#c69c6d"))
        b.parts_3d.append(Part3D("Front wall R", door_x0 + DOOR_W, 0, wall_z,
                                 W - door_x0 - DOOR_W, STUD_T, WH, "#c69c6d"))
        b.parts_3d.append(Part3D("Door header", door_x0, 0, wall_z + door_h,
                                 DOOR_W, STUD_T, WH - door_h, "#c69c6d"))
        b.parts_3d.append(Part3D("Door", door_x0 + 1, -0.75, wall_z,
                                 DOOR_W - 2, 0.75, door_h, "#8b5a2b"))
        b.parts_3d.append(Part3D("Back wall", 0, D - STUD_T, wall_z, W, STUD_T, WH, "#c69c6d"))
        b.parts_3d.append(Part3D("Left wall", 0, STUD_T, wall_z, STUD_T, D - 2 * STUD_T, WH, "#c69c6d"))
        b.parts_3d.append(Part3D("Right wall", W - STUD_T, STUD_T, wall_z, STUD_T, D - 2 * STUD_T, WH, "#c69c6d"))
        # Gable ends: stacked, narrowing slabs up to the ridge
        top_z = wall_z + WH
        GABLE_STEPS = 6
        for i in range(GABLE_STEPS):
            frac0 = i / GABLE_STEPS
            step_h = rise / GABLE_STEPS
            inset = run * frac0
            width_i = W - 2 * inset
            if width_i <= 4:
                continue
            for yy, label in ((0, "Front gable"), (D - STUD_T, "Back gable")):
                b.parts_3d.append(Part3D(f"{label} {i+1}", inset, yy, top_z + i * step_h,
                                         width_i, STUD_T, step_h, "#b58b62"))
        # Pitched roof: stair-stepped slabs climbing to the ridge on both sides
        ROOF_STEPS = 8
        step_run = (run + 4) / ROOF_STEPS   # +4" eave overhang
        step_rise = rise / ROOF_STEPS
        roof_t = 1.6
        for i in range(ROOF_STEPS):
            x_off = -4 + i * step_run
            z_off = top_z - 2 + i * step_rise
            # Left slope
            b.parts_3d.append(Part3D(f"Roof L{i+1}", x_off, -2, z_off,
                                     step_run + 1.5, D + 4, roof_t, "#57534e"))
            # Right slope (mirror)
            b.parts_3d.append(Part3D(f"Roof R{i+1}", W - x_off - step_run - 1.5, -2, z_off,
                                     step_run + 1.5, D + 4, roof_t, "#57534e"))
        # Ridge cap
        b.parts_3d.append(Part3D("Ridge", W / 2 - 2, -2, top_z + rise - 1,
                                 4, D + 4, 2, "#44403c"))

        b.notes.append("Check local building codes — many areas allow sheds under ~120 sq ft permit-free, but always verify.")
        b.notes.append("Set the foundation skids on a level gravel pad. A level shed lasts decades; an unlevel one racks and sags.")
        b.assembly_hints = {
            "width_in": W, "depth_in": D, "wall_height_in": WH,
            "roof_pitch": PITCH, "door_width_in": DOOR_W,
            "n_joists": n_joists, "n_rafter_pairs": n_rafter_pairs,
        }
        return b
