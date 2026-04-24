# Builtit — DIY Carpentry Generator

A working MVP of an app that generates buildable DIY carpentry projects: pick a
project, set your dimensions, and get back a 3D model, a shopping list with
realistic prices, an optimized cut diagram, and step-by-step beginner
instructions.

This is the foundation for a business product — extend it with more project
types, real price scraping, and AI-assisted price optimization.

## What's in the MVP

Three project templates, fully parametric:

- **Bookshelf** — 1x12 pine + plywood back. ~$140-200 depending on size.
- **Simple Desk** — 4x4 legs, 1x4 aprons, plywood top with edge banding. ~$180-250.
- **Storage Shed** — Stick-framed walls, OSB sheathing, asphalt roof. ~$700-1200.

For each project the API returns:
- A 3D model (axis-aligned boxes for fast in-browser rendering)
- A cut list (pieces of dimensional lumber to cut)
- Sheet-good cuts (plywood / OSB)
- An optimized **shopping list** that bin-packs cuts onto the cheapest stock
  lengths, accounting for kerf
- **Cut diagrams** showing exactly how to lay out cuts on each board
- Step-by-step beginner instructions with tool list, time estimates, and safety notes

## Architecture

```
diy-builder/
├── backend/                  Python + FastAPI
│   ├── app/
│   │   ├── data/catalog.json    Mock materials catalog (lumber, panels, hardware)
│   │   ├── models/              Parametric project models (bookshelf, desk, shed)
│   │   ├── services/
│   │   │   ├── catalog.py       Catalog lookup
│   │   │   ├── cutlist.py       Bin-packing cut optimizer + shopping list builder
│   │   │   └── instructions.py  Step-by-step instruction generator
│   │   ├── tests/               Pytest suite
│   │   └── main.py              FastAPI app
│   └── requirements.txt
├── frontend/
│   └── index.html            Single-file React + Three.js UI (Tailwind via CDN)
├── run_all.py                One-command runner: backend + frontend proxy
└── README.md
```

### Why this layout
- **Backend separated** because the modeling logic, the cut optimizer, and the
  scraper-of-the-future are all server-side concerns. Keeps the math testable
  and lets you swap UIs later (mobile, desktop) without rewriting domain logic.
- **Frontend in a single HTML file** for the MVP — zero build step, opens in any
  browser. When you're ready to scale, drop the same React components into a
  Vite project. Nothing locks you in.

## Running it

You need Python 3.10+ and a modern browser.

```bash
cd diy-builder
pip install -r backend/requirements.txt
python run_all.py
```

Then open http://localhost:5173 in your browser.

`run_all.py` starts the FastAPI server on port 8000 and a static file server
on port 5173 that proxies `/api/*` requests to the backend. Single command,
single port to remember.

### Running pieces separately

If you'd rather run the backend on its own:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
# Then open frontend/index.html directly — it'll auto-detect file:// and use http://localhost:8000
```

### Tests

```bash
cd backend
python -m pytest app/tests --basetemp=/tmp/pyt
```

## API surface

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness probe |
| GET | `/api/projects` | List project templates with parameter schemas |
| GET | `/api/projects/{id}` | Get one project's schema |
| POST | `/api/projects/{id}/generate` | Generate a complete build. Body: `{"parameters": {...}}` |

The `generate` response has these top-level keys:
`project`, `parameters`, `model_3d`, `cuts`, `panels`, `shopping_list`,
`instructions`, `notes`.

## How the cut optimizer works

For each nominal lumber size in the build (1x12, 2x4, etc.), the optimizer:
1. Finds all stock lengths in the catalog matching that nominal size.
2. Picks the stock with the lowest cost-per-inch that can still fit the longest cut.
3. Bin-packs the requested cuts onto stock pieces using **first-fit decreasing**,
   accounting for a 1/8" saw kerf between cuts.
4. Counts boards needed and calculates total cost.

It's not optimal (true 1D bin packing is NP-hard), but FFD gets within ~98% of
optimal for typical project sizes and runs in milliseconds. The bookshelf
example packs 7 cuts onto 3 boards with ~90% material utilization.

## How instructions are generated

Each project has a hand-tuned step list in `services/instructions.py`. The steps
are *parameterized* — the model's `assembly_hints` (number of shelves, dimensions,
etc.) get interpolated into the instruction text so numbers always match what the
user actually configured. This keeps the instructions accurate and personal
without requiring an LLM in the loop.

For more nuanced instructions later, this is the natural place to plug in an LLM
that takes the build + user skill level and produces richer guidance.

## Roadmap

### Near-term
- **More project templates**: chair, cabinet, dog house, raised garden bed,
  workbench, picnic table.
- **Price optimization**: when a cut requires lumber, evaluate every viable
  stock length × vendor combination and pick the lowest-total-cost packing.
  The current optimizer minimizes board count for a *given* stock; this would
  go one level higher and pick the stock to minimize total spend.
- **Multi-vendor pricing**: same item from Home Depot vs. Lowe's vs. Amazon.
  Show the savings and let users pick a vendor preference.
- **Skill-level toggle**: "first-time builder" vs. "comfortable with tools" —
  expand or compress instruction detail accordingly.
- **Persistent saved builds**: user accounts, save & share builds via URL.

### Medium-term
- **Real pricing data**: Home Depot's product catalog is large but well-structured.
  Options: (a) Home Depot's affiliate API, (b) Amazon Product Advertising API,
  (c) a paid lumber-pricing data provider like SPLRT or Leadwerks. Pure scraping
  is fragile and against most ToS.
- **Cut-list PDF export**: print-friendly cut diagrams + shopping list to take
  to the store.
- **Integration with delivery**: one-click order from Home Depot / Lowe's
  with the full shopping list pre-populated.

### Long-term / vision
- **3D parametric editor**: drag a face to resize, see the cost update live.
- **Photo → project**: snap a photo of a piece of furniture, get back a buildable
  approximation. (Vision model + parametric matcher.)
- **Local pickup**: integrate with neighborhood-level lumber availability.
- **Mobile companion**: phone shows the next step + a photo as you build.

## Notes for the founder

- **Pricing data is the moat** for this kind of product. Build a great
  pricing pipeline (catalog updates daily, multi-vendor, accurate stock checks)
  and the rest is execution.
- **The cut optimizer is your wow-factor** — most DIYers either guess board
  count and over-buy, or do the math by hand. Getting this right + showing
  the savings is the demo moment.
- **Don't underestimate instructions.** The difference between "buildable" and
  "intimidating" is mostly the quality of the step-by-step. Consider partnering
  with carpenters/YouTubers to record short clips per step.
- **Watch out for the building-code rabbit hole.** Sheds and tree houses can
  trigger permits in many jurisdictions. The current MVP includes a warning
  in the shed notes; production should ask the user's location and pull
  permit thresholds.
