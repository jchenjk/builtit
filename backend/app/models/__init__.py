"""Parametric carpentry models.

Each model defines:
  - id, name, description, difficulty
  - parameter schema (JSON-Schema-ish, simple)
  - a generate(params) function that returns a Build:
      - components: list of named parts with cuts (length/width/thickness/qty)
      - panels: sheet-good cuts (LxW, qty, thickness)
      - hardware: list of (catalog_id, qty) for fasteners/hinges/etc.
      - parts_3d: simple boxes [x,y,z, dx,dy,dz, color, label] for visualization

The downstream services pack cuts onto stock lumber, tally hardware, and
emit instructions.
"""
from .bookshelf import BookshelfModel
from .desk import DeskModel
from .shed import ShedModel

ALL_MODELS = {m.id: m for m in [BookshelfModel, DeskModel, ShedModel]}
