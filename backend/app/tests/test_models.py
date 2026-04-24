"""Sanity checks on each model + cut-list + instructions."""
from app.models import ALL_MODELS
from app.services.cutlist import build_shopping_list
from app.services.instructions import generate_instructions


def test_all_projects_generate_with_defaults():
    for pid, model in ALL_MODELS.items():
        defaults = {p.key: p.default for p in model.params}
        build = model.generate(defaults)
        assert build.cuts or build.panels, f"{pid} produced no cuts or panels"
        assert build.parts_3d, f"{pid} has no 3D parts"


def test_shopping_list_for_each_project():
    for pid, model in ALL_MODELS.items():
        defaults = {p.key: p.default for p in model.params}
        build = model.generate(defaults)
        sl = build_shopping_list(build)
        assert sl["lines"], f"{pid} produced empty shopping list"
        assert sl["total_cost"] > 0, f"{pid} total cost should be > 0"
        # Every line has a positive qty and price
        for line in sl["lines"]:
            assert line["qty"] >= 1
            assert line["unit_price"] > 0
            assert line["line_cost"] >= line["unit_price"]


def test_instructions_for_each_project():
    for pid, model in ALL_MODELS.items():
        defaults = {p.key: p.default for p in model.params}
        build = model.generate(defaults)
        sl = build_shopping_list(build)
        ins = generate_instructions(pid, build, sl)
        assert ins["steps"], f"{pid} produced no steps"
        # Steps should be numbered consecutively from 1
        nums = [s["step"] for s in ins["steps"]]
        assert nums == list(range(1, len(nums) + 1)), f"{pid} steps not 1..N"
        assert ins["estimated_total_minutes"] > 0


def test_bookshelf_scales_with_shelves():
    M = ALL_MODELS["bookshelf"]
    b1 = M.generate({"width_in": 30, "height_in": 60, "shelves": 2})
    b2 = M.generate({"width_in": 30, "height_in": 60, "shelves": 5})
    # More shelves => more horizontal cuts
    cuts1 = sum(c.qty for c in b1.cuts if "shelf" in c.name.lower())
    cuts2 = sum(c.qty for c in b2.cuts if "shelf" in c.name.lower())
    assert cuts2 > cuts1


def test_shed_uses_treated_lumber_for_skids():
    M = ALL_MODELS["shed"]
    defaults = {p.key: p.default for p in M.params}
    build = M.generate(defaults)
    skid_cuts = [c for c in build.cuts if "skid" in c.name.lower()]
    assert skid_cuts, "shed should have foundation skids"
    assert all(c.nominal == "4x4" for c in skid_cuts)


def test_cutlist_packs_efficiently():
    """A bookshelf with several short cuts should pack onto few stock pieces."""
    M = ALL_MODELS["bookshelf"]
    build = M.generate({"width_in": 30, "height_in": 60, "shelves": 3})
    sl = build_shopping_list(build)
    # 5 horizontal cuts at ~28.5 in. each fit easily on a single 96 in. board
    one_x_twelve = next(l for l in sl["lines"] if l["details"].get("nominal") == "1x12")
    # 2 sides at 60 in. each + 5 horizontals at ~28.5 in. each
    # 2 stocks needed at minimum (sides take 60 in. each, leaving 36 in. for 1 horizontal each)
    # FFD should give us roughly 3-4 boards, not 7
    assert one_x_twelve["qty"] <= 5, f"expected efficient packing, got {one_x_twelve['qty']} boards"
