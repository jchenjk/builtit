"""FastAPI app: DIY Builder backend."""
import os
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any

from .models import ALL_MODELS
from .services.cutlist import build_shopping_list
from .services.instructions import generate_instructions
from .services.pricing import get_live_prices, live_pricing_available

app = FastAPI(
    title="DIY Builder API",
    description=(
        "Generate parametric DIY carpentry projects: 3D model, cut list, "
        "shopping list, and step-by-step beginner instructions."
    ),
    version="0.1.0",
)

# Allow the React dev server to hit the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for the MVP/dev. Lock down in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/projects")
def list_projects():
    """List all available project templates with their schemas."""
    return {"projects": [m.schema() for m in ALL_MODELS.values()]}


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    model = ALL_MODELS.get(project_id)
    if model is None:
        raise HTTPException(404, f"Unknown project: {project_id}")
    return model.schema()


class GenerateRequest(BaseModel):
    parameters: dict[str, Any] = {}


@app.post("/api/projects/{project_id}/generate")
def generate(project_id: str, req: GenerateRequest):
    """Generate a complete build for the given parameters."""
    model = ALL_MODELS.get(project_id)
    if model is None:
        raise HTTPException(404, f"Unknown project: {project_id}")

    build = model.generate(req.parameters)
    shopping = build_shopping_list(build)
    instructions = generate_instructions(project_id, build, shopping)

    return {
        "project": model.schema(),
        "parameters": model.coerce(req.parameters),
        "model_3d": {
            "parts": [asdict(p) for p in build.parts_3d],
            # bounding box for the camera to frame
            "bbox": _bbox(build.parts_3d),
        },
        "cuts": [asdict(c) for c in build.cuts],
        "panels": [asdict(p) for p in build.panels],
        "shopping_list": shopping,
        "instructions": instructions,
        "notes": build.notes,
    }


class LivePricesRequest(BaseModel):
    catalog_ids: list[str]
    zip_code: str | None = Field(default=None, pattern=r"^\d{5}$")


@app.get("/api/prices/status")
def prices_status():
    """Whether live Home Depot pricing is configured (SERPAPI_KEY set)."""
    return {"live_enabled": live_pricing_available()}


@app.post("/api/prices/live")
async def live_prices(req: LivePricesRequest):
    """Fetch live Home Depot quotes for shopping-list items.

    Falls back to built-in catalog prices per-item when live lookup fails
    or no SERPAPI_KEY is configured.
    """
    if not req.catalog_ids:
        raise HTTPException(400, "catalog_ids must not be empty")
    if len(req.catalog_ids) > 40:
        raise HTTPException(400, "Too many items (max 40)")
    return await get_live_prices(req.catalog_ids, req.zip_code)


def _bbox(parts):
    if not parts:
        return {"min": [0, 0, 0], "max": [1, 1, 1]}
    xs = [p.x for p in parts] + [p.x + p.dx for p in parts]
    ys = [p.y for p in parts] + [p.y + p.dy for p in parts]
    zs = [p.z for p in parts] + [p.z + p.dz for p in parts]
    return {"min": [min(xs), min(ys), min(zs)],
            "max": [max(xs), max(ys), max(zs)]}


# Serve the frontend from the same process in production (Render, etc.).
# Mounted last so /api/* routes take priority.
_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
