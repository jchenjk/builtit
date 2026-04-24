"""Cut-list optimizer + materials calculator.

For each nominal lumber size requested by a build, picks the best stock
length and bin-packs cuts onto stock pieces using a first-fit-decreasing
heuristic. Then aggregates hardware and panels into a shopping list with
realistic counts and an estimated cost.
"""
from collections import defaultdict
from .catalog import items_by_nominal, get_item

# Saw blade kerf — material wasted per cut (1/8" is typical for a circular saw)
KERF_IN = 0.125


def _ffd_pack(cut_lengths: list[float], stock_len: float) -> list[list[float]]:
    """First-fit decreasing bin packing. Returns list of bins (stock pieces),
    each a list of cut lengths placed on that piece. Accounts for kerf."""
    # Sort largest first
    cuts = sorted(cut_lengths, reverse=True)
    bins: list[list[float]] = []
    bin_used: list[float] = []  # used length per bin (incl. kerf)
    for c in cuts:
        if c > stock_len:
            # Cut is longer than available stock — flag it as its own bin and
            # let the UI surface the issue. Should not happen with our params.
            bins.append([c])
            bin_used.append(c)
            continue
        placed = False
        for i, used in enumerate(bin_used):
            extra_kerf = KERF_IN if bins[i] else 0
            if used + extra_kerf + c <= stock_len:
                bins[i].append(c)
                bin_used[i] = used + extra_kerf + c
                placed = True
                break
        if not placed:
            bins.append([c])
            bin_used.append(c)
    return bins


def _pick_stock_for_nominal(nominal: str, max_cut_len: float) -> dict | None:
    """Choose a stock length: smallest available stock that fits the longest cut."""
    options = items_by_nominal(nominal)
    feasible = [o for o in options if o["length_in"] >= max_cut_len]
    if not feasible:
        return options[-1] if options else None  # fallback to longest
    # Cheapest cost-per-inch among feasible
    return min(feasible, key=lambda o: o["price"] / o["length_in"])


def build_shopping_list(build) -> dict:
    """Given a Build dataclass, return a shopping list dict."""
    # Aggregate cuts by nominal
    by_nominal: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for cut in build.cuts:
        for _ in range(cut.qty):
            by_nominal[cut.nominal].append((cut.length_in, cut.name))

    lumber_lines = []
    for nominal, cut_pairs in by_nominal.items():
        cut_lens = [c[0] for c in cut_pairs]
        max_cut = max(cut_lens)
        stock = _pick_stock_for_nominal(nominal, max_cut)
        if stock is None:
            continue
        bins = _ffd_pack(cut_lens, stock["length_in"])
        n_stock = len(bins)
        line_cost = round(n_stock * stock["price"], 2)
        # Brief packing summary
        utilization = sum(sum(b) for b in bins) / (n_stock * stock["length_in"]) if n_stock else 0
        lumber_lines.append({
            "kind": "lumber",
            "catalog_id": stock["id"],
            "name": stock["name"],
            "vendor": stock["vendor"],
            "qty": n_stock,
            "unit_price": stock["price"],
            "line_cost": line_cost,
            "details": {
                "nominal": nominal,
                "cuts_total": len(cut_lens),
                "longest_cut_in": max_cut,
                "stock_length_in": stock["length_in"],
                "utilization_pct": round(utilization * 100, 1),
                "kerf_in": KERF_IN,
            },
        })

    # Panels — for each unique thickness, count sheets (assume sheet = 4x8 = 4608 sqin)
    panel_lines = []
    panels_by_thickness: dict[float, list] = defaultdict(list)
    for panel in build.panels:
        for _ in range(panel.qty):
            panels_by_thickness[panel.thickness_in].append(panel)
    for thick, plist in panels_by_thickness.items():
        # Pick a sheet from the catalog matching this thickness
        sheet_item = next(
            (i for i in items_by_nominal_alt_panels(thick)), None
        )
        if sheet_item is None:
            continue
        sheet_area = sheet_item["sheet_in"][0] * sheet_item["sheet_in"][1]
        # Approximate by total area + 15% waste factor for cuts
        total_area = sum(p.length_in * p.width_in for p in plist)
        sheets_needed = max(1, int(-(-int(total_area * 1.15) // sheet_area)))
        # The above can underestimate when single panel > sheet; bump if so
        for p in plist:
            if p.length_in > sheet_item["sheet_in"][1] or p.width_in > sheet_item["sheet_in"][0]:
                sheets_needed = max(sheets_needed, len(plist))
        line_cost = round(sheets_needed * sheet_item["price"], 2)
        panel_lines.append({
            "kind": "panel",
            "catalog_id": sheet_item["id"],
            "name": sheet_item["name"],
            "vendor": sheet_item["vendor"],
            "qty": sheets_needed,
            "unit_price": sheet_item["price"],
            "line_cost": line_cost,
            "details": {
                "thickness_in": thick,
                "pieces_to_cut": len(plist),
                "total_area_sqin": int(total_area),
                "waste_factor_pct": 15,
            },
        })

    # Hardware — aggregate by catalog_id, then convert qty to packs
    hw_qty: dict[str, int] = defaultdict(int)
    hw_notes: dict[str, list[str]] = defaultdict(list)
    for h in build.hardware:
        hw_qty[h.catalog_id] += h.qty
        if h.notes:
            hw_notes[h.catalog_id].append(h.notes)

    hardware_lines = []
    for cid, q in hw_qty.items():
        item = get_item(cid)
        if item is None:
            continue
        per = item.get("count_per_unit", 1)
        # For coverage items (felt/poly), q is already in "units" (1 = one roll/quart)
        if item.get("kind") == "coverage":
            packs = max(1, q)
        else:
            packs = max(1, -(-q // per))  # ceiling division
        line_cost = round(packs * item["price"], 2)
        hardware_lines.append({
            "kind": "hardware",
            "catalog_id": cid,
            "name": item["name"],
            "vendor": item["vendor"],
            "qty": packs,
            "unit_price": item["price"],
            "line_cost": line_cost,
            "details": {
                "needed_count": q,
                "count_per_unit": per,
                "notes": "; ".join(hw_notes[cid]) if hw_notes[cid] else "",
            },
        })

    all_lines = lumber_lines + panel_lines + hardware_lines
    total = round(sum(l["line_cost"] for l in all_lines), 2)

    # Build the cut-list per stock piece for instructions
    cut_diagrams = []
    for line in lumber_lines:
        nominal = line["details"]["nominal"]
        # Reproduce packing to expose per-piece layout
        cuts = [(c, name) for c in []
                for name in []]  # placeholder; we'll redo properly below
    cut_diagrams = _build_cut_diagrams(build, lumber_lines)

    return {
        "lines": all_lines,
        "total_cost": total,
        "currency": "USD",
        "cut_diagrams": cut_diagrams,
    }


def items_by_nominal_alt_panels(thickness_in: float) -> list[dict]:
    """Find sheet-good catalog items matching a thickness, preferring plywood."""
    from .catalog import load_catalog
    items = [i for i in load_catalog()["items"]
             if i.get("kind") == "sheet" and abs(i.get("thickness_in", -1) - thickness_in) < 1e-3]
    # Prefer plywood over OSB for cabinet-grade work; otherwise just first match.
    return sorted(items, key=lambda i: 0 if "plywood" in i["id"] else 1)


def _build_cut_diagrams(build, lumber_lines):
    """For each lumber line, produce a list of stock pieces with the cuts on each."""
    diagrams = []
    by_nominal = defaultdict(list)
    for cut in build.cuts:
        for _ in range(cut.qty):
            by_nominal[cut.nominal].append((cut.length_in, cut.name))

    for line in lumber_lines:
        nominal = line["details"]["nominal"]
        stock_len = line["details"]["stock_length_in"]
        cut_pairs = by_nominal.get(nominal, [])
        # FFD again but track names too
        sorted_pairs = sorted(cut_pairs, key=lambda x: -x[0])
        bins: list[list[tuple[float, str]]] = []
        used: list[float] = []
        for length, name in sorted_pairs:
            placed = False
            for i, u in enumerate(used):
                extra = KERF_IN if bins[i] else 0
                if u + extra + length <= stock_len:
                    bins[i].append((length, name))
                    used[i] = u + extra + length
                    placed = True
                    break
            if not placed:
                bins.append([(length, name)])
                used.append(length)
        diagrams.append({
            "stock_name": line["name"],
            "stock_length_in": stock_len,
            "pieces": [
                {
                    "stock_index": i + 1,
                    "cuts": [{"length_in": l, "name": n} for (l, n) in bin_],
                    "leftover_in": round(stock_len - used[i] - max(0, (len(bin_) - 1) * KERF_IN), 2),
                }
                for i, bin_ in enumerate(bins)
            ],
        })
    return diagrams
