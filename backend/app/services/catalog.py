"""Loads the materials catalog and provides lookup helpers."""
import json
import os
from functools import lru_cache

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "catalog.json"
)


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


def get_item(item_id: str) -> dict | None:
    return next((i for i in load_catalog()["items"] if i["id"] == item_id), None)


def items_by_nominal(nominal: str) -> list[dict]:
    """Return all stock-lumber items with a given nominal size, sorted by length asc."""
    items = [i for i in load_catalog()["items"]
             if i.get("nominal") == nominal and i.get("kind") == "board"]
    return sorted(items, key=lambda i: i["length_in"])
