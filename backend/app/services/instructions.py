"""Step-by-step assembly instructions, written for absolute beginners.

Each project has its own ordered set of steps. Steps are generated from the
build hints + cut list so numbers (e.g., "drive 12 screws") match the
shopping list exactly.
"""
from typing import Any


COMMON_TOOLS = [
    "Tape measure",
    "Pencil and combination square",
    "Circular saw or miter saw",
    "Cordless drill / driver",
    "1/8 in. drill bit (for pilot holes)",
    "Safety glasses and ear protection",
    "Clamps (a few bar clamps help a lot)",
]

COMMON_SAFETY = [
    "Always wear safety glasses when cutting or driving fasteners.",
    "Cut on a stable surface; never freehand a long board across sawhorses without support on both sides.",
    "Keep fingers behind the saw blade and let the blade reach full speed before the cut.",
    "Pre-drill pilot holes near the ends of boards to prevent splitting.",
]


def _step(num: int, title: str, body: str, est_min: int = 15) -> dict:
    return {"step": num, "title": title, "body": body, "estimated_minutes": est_min}


def generate_instructions(project_id: str, build, shopping_list: dict) -> dict:
    if project_id == "bookshelf":
        steps = _bookshelf_steps(build, shopping_list)
        tools = COMMON_TOOLS + ["Square (for checking 90° corners)"]
    elif project_id == "desk":
        steps = _desk_steps(build, shopping_list)
        tools = COMMON_TOOLS + ["Sander (or sanding block)", "Foam brush for finish"]
    elif project_id == "shed":
        steps = _shed_steps(build, shopping_list)
        tools = COMMON_TOOLS + [
            "Speed square (for marking rafter angles)",
            "Hammer (for framing nails)",
            "Ladder",
            "Utility knife (for shingles and felt)",
            "4-ft level",
        ]
    else:
        steps = []
        tools = COMMON_TOOLS

    total_min = sum(s["estimated_minutes"] for s in steps)
    return {
        "tools": tools,
        "safety": COMMON_SAFETY,
        "steps": steps,
        "estimated_total_minutes": total_min,
        "tips": [n for n in build.notes],
    }


# ---------- Project-specific step writers ----------

def _bookshelf_steps(build, shopping_list) -> list[dict]:
    h = build.assembly_hints
    shelves = h["shelves"]
    total_shelves = 2 + shelves
    return [
        _step(1, "Lay out and mark all cuts",
              f"Mark every cut with a pencil and a square. You'll cut: 2 side panels at "
              f"{h['height_in']:.0f} in., and {total_shelves} horizontal pieces at "
              f"{(h['width_in'] - 1.5):.2f} in. (the inside width). Marking everything before "
              f"cutting saves trips back and forth.",
              est_min=20),
        _step(2, "Make all the cuts",
              "Cut the 2 side panels first, then cut all horizontal pieces stacked together "
              "or set up a stop block on your saw — this guarantees they're identical, which is "
              "what makes the shelf look square.",
              est_min=30),
        _step(3, "Sand all surfaces",
              "Sand every surface with 120 grit, then 220 grit. Pay extra attention to edges and "
              "ends. Don't skip this — it's the difference between 'amateur' and 'looks bought'.",
              est_min=30),
        _step(4, "Mark shelf positions on the side panels",
              f"Lay both side panels next to each other. Measure from the bottom and mark where "
              f"each of the {shelves} interior shelves will sit. Equal spacing looks best — "
              f"divide the inside height by {shelves + 1} and mark.",
              est_min=15),
        _step(5, "Build the box (top + bottom + sides)",
              "Stand a side panel on edge. Run a thin bead of wood glue along the end. Set the "
              "bottom shelf flush with the bottom edge. Pre-drill 3 pilot holes through the side "
              "into the end of the bottom, then drive 3 screws. Repeat for the top, then the "
              "other side panel.",
              est_min=30),
        _step(6, "Install the interior shelves",
              "With the box on its back, dry-fit each interior shelf on its marks. Glue, "
              "pre-drill, and screw — 3 screws per side, per shelf. Check for square as you go "
              "by measuring corner-to-corner diagonals; they should be equal.",
              est_min=30),
        _step(7, "Attach the back panel" if h["include_back"] else "Inspect and tighten",
              ("Lay the bookshelf face-down. Set the plywood back on top, flush with the edges. "
               "Drive a 1-1/4 in. screw every ~6 in. around the perimeter and into each shelf. "
               "The back is what keeps the shelf from racking — don't skip screws.")
              if h["include_back"]
              else "Walk around the bookshelf, tighten any screws that didn't fully seat, and check that all joints are tight.",
              est_min=20 if h["include_back"] else 10),
        _step(8, "Apply finish",
              "Wipe off all dust with a tack cloth or damp rag. Apply your finish of choice — "
              "polyurethane for protection, a stain + poly for color, or just leave it raw and "
              "natural. Two coats with a light 220-grit sanding between coats is plenty.",
              est_min=45),
        _step(9, "Anchor to the wall",
              "Tall bookshelves can tip. Drive 2 screws through the back panel into wall studs "
              "near the top. This is a 5-minute job that prevents a serious accident.",
              est_min=10),
    ]


def _desk_steps(build, shopping_list) -> list[dict]:
    h = build.assembly_hints
    return [
        _step(1, "Cut all parts",
              f"Cut 4 legs to {(h['height_in'] - 0.75):.2f} in. (desk height minus the 3/4 in. top). "
              f"Cut 2 long aprons at {(h['width_in'] - 7):.2f} in. and 2 short aprons at "
              f"{(h['depth_in'] - 7):.2f} in. Cut the {h['width_in']:.0f} x {h['depth_in']:.0f} in. "
              "tabletop from your plywood sheet.",
              est_min=45),
        _step(2, "Sand everything",
              "Hit every surface with 120 grit then 220 grit. Round over the sharp edges of the "
              "tabletop slightly — your wrists will thank you later.",
              est_min=40),
        _step(3, "Build the leg-and-apron frame",
              "Lay 2 legs flat on a workbench. Set a long apron between them, flush with the top. "
              "Apply glue, clamp, pre-drill, and drive two 3 in. screws through the leg into the "
              "apron at each joint. Repeat with the other 2 legs and second long apron.",
              est_min=30),
        _step(4, "Connect the two leg pairs",
              "Stand both leg pairs upright. Set the short aprons between them at the same height "
              "as the long aprons. Glue, clamp, drill, screw. Check that everything is square by "
              "measuring corner-to-corner at the floor — diagonals should match.",
              est_min=25),
        _step(5, "Attach the tabletop",
              "Center the tabletop on the frame — overhang should be equal on all sides. From "
              "underneath, drive 2 in. screws up through the aprons into the top. Use 3 screws "
              "per apron. Don't go all the way through!",
              est_min=20),
        _step(6, "Add edge banding",
              "Glue and pin (or screw from underneath) the 1x4 edge banding around the perimeter "
              "of the tabletop. This hides the plywood edge and gives the desk a chunky, "
              "intentional look.",
              est_min=30),
        _step(7, "Finish",
              "Wipe down with a tack cloth. Apply 2-3 coats of polyurethane to the tabletop "
              "(it'll see coffee, mouse pads, sweaty palms). One coat on legs and aprons is fine.",
              est_min=60),
    ]


def _shed_steps(build, shopping_list) -> list[dict]:
    h = build.assembly_hints
    return [
        _step(1, "Pick the site and prep the ground",
              "Choose a flat spot with good drainage. Mark out the footprint "
              f"({h['width_in']/12:.0f} ft x {h['depth_in']/12:.0f} ft) with stakes and string. "
              "Excavate ~4 in. of soil and lay down a level bed of crushed gravel. A level base "
              "is the single most important thing for a shed that lasts.",
              est_min=180),
        _step(2, "Set the foundation skids",
              "Place the 2 pressure-treated 4x4 skids on the gravel bed, parallel and level "
              "with each other. Use a long board with a level on top to check across them.",
              est_min=45),
        _step(3, "Build the floor frame",
              f"Lay out the {h['n_joists']} floor joists across the skids at 16 in. on center. "
              "Nail or screw them to the front and back rim joists, then attach the assembly to "
              "the skids with deck screws.",
              est_min=90),
        _step(4, "Install the floor decking",
              "Lay the plywood floor sheets across the joists, staggered if you're using more "
              "than one row. Screw down every 8 in. along edges and 12 in. in the field.",
              est_min=45),
        _step(5, "Frame the four walls",
              "Build each wall flat on the floor: bottom plate, top plate, studs at 16 in. on "
              "center. The front wall has a rough opening for the door — install jack studs on "
              "either side and a header across the top. Stand each wall up, plumb it, and nail "
              "it to the floor. Connect corners.",
              est_min=240),
        _step(6, "Add the double top plate",
              "Lay a second 2x4 on top of each top plate, overlapping the corners. This ties "
              "all four walls together and gives the rafters something solid to land on.",
              est_min=30),
        _step(7, "Cut and install rafters",
              f"Cut a pattern rafter with the correct {h['roof_pitch']}/12 plumb cut at the peak "
              f"and a birdsmouth where it meets the wall plate. Test-fit, then use it as a "
              f"template for the rest. Install the ridge board, then {h['n_rafter_pairs']} pairs "
              "of rafters at 24 in. on center.",
              est_min=180),
        _step(8, "Sheath the walls and roof",
              "Cover the walls with OSB, screwed to studs every 8 in. on edges and 12 in. in "
              "the field. Cut openings for the door. Then sheath the roof the same way, working "
              "from the bottom up so each row supports the next.",
              est_min=180),
        _step(9, "Roof: felt then shingles",
              "Roll out roofing felt horizontally, starting at the bottom edge, overlapping each "
              "row by ~4 in. Then install shingles from the bottom up, staggering joints. Use 4 "
              "roofing nails per shingle.",
              est_min=240),
        _step(10, "Build and hang the door",
              f"Build the door from a 2x4 frame ({h['door_width_in']:.0f} in. wide) sheathed with "
              "OSB. Install hinges on the door, then hang it in the rough opening. Add a handle "
              "and latch.",
              est_min=120),
        _step(11, "Trim, paint, and call it done",
              "Add 1x4 corner trim and trim around the door for a finished look. Prime and paint "
              "(or stain) the OSB to protect it from weather — bare OSB will swell.",
              est_min=240),
    ]
