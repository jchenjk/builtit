"""Live material pricing.

Provider architecture:
- SerpApiHomeDepotProvider — real-time Home Depot prices via SerpApi
  (https://serpapi.com/home-depot-search-api). Needs SERPAPI_KEY env var.
- CatalogProvider — fallback that returns the built-in catalog price, so the
  app works with no API key and degrades gracefully when SerpApi errors out.

Results are cached in-memory with a TTL so repeated builds don't burn API
credits (SerpApi free tier = 100 searches/month).
"""
import asyncio
import os
import re
import time

import httpx

from .catalog import get_item

SERPAPI_URL = "https://serpapi.com/search.json"
CACHE_TTL_SECONDS = 6 * 3600  # prices don't move fast; 6h keeps credits low
REQUEST_TIMEOUT = 15.0

# catalog_id -> search query tuned for Home Depot's search engine.
# Falls back to a cleaned-up catalog name for ids not listed here.
SEARCH_QUERIES = {
    "lumber.2x4.8ft.spf": "2x4x8 stud",
    "lumber.2x4.10ft.spf": "2x4x10 lumber",
    "lumber.2x6.8ft.spf": "2x6x8 lumber",
    "lumber.2x6.10ft.spf": "2x6x10 lumber",
    "lumber.4x4.8ft.treated": "4x4x8 pressure treated post",
    "lumber.1x12.8ft.pine": "1x12x8 pine board",
    "lumber.1x12.6ft.pine": "1x12x6 pine board",
    "lumber.1x4.8ft.pine": "1x4x8 pine board",
    "panel.plywood.0.5in.4x8.sanded": "1/2 in sanded plywood 4x8",
    "panel.plywood.0.75in.4x8": "3/4 in plywood 4x8",
    "panel.osb.7-16in.4x8": "7/16 osb sheathing 4x8",
    "roofing.shingles.bundle": "asphalt shingles bundle",
    "roofing.felt.15lb.roll": "15 lb roofing felt roll",
    "fastener.screws.deck.3in.5lb": "3 in exterior deck screws 5 lb",
    "fastener.screws.wood.1.25in.1lb": "1-1/4 in wood screws 1 lb",
    "fastener.screws.wood.2in.1lb": "2 in wood screws 1 lb",
    "fastener.nails.framing.16d.5lb": "16d framing nails 5 lb",
    "fastener.nails.roofing.1.25in.1lb": "1-1/4 in roofing nails",
    "hardware.hinge.3.5in.pair": "3-1/2 in door hinge",
    "hardware.handle.barn": "barn door handle",
    "hardware.bracket.shelf.pair": "heavy duty shelf bracket",
    "finish.woodglue.16oz": "wood glue 16 oz",
    "finish.sandpaper.assorted": "sandpaper assorted pack",
    "finish.polyurethane.qt": "polyurethane clear quart",
}

# --- tiny in-memory TTL cache -------------------------------------------------
_cache: dict[str, tuple[float, dict]] = {}


def _cache_get(key: str) -> dict | None:
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    return None


def _cache_put(key: str, value: dict) -> None:
    _cache[key] = (time.time(), value)


# --- providers ----------------------------------------------------------------
def _search_query_for(catalog_id: str) -> str | None:
    if catalog_id in SEARCH_QUERIES:
        return SEARCH_QUERIES[catalog_id]
    item = get_item(catalog_id)
    if item is None:
        return None
    # Strip parentheticals from the catalog name: "1x12 Pine Board, 8 ft (...)"
    return re.sub(r"\s*\(.*?\)", "", item["name"]).strip()


def _catalog_quote(catalog_id: str) -> dict | None:
    """Fallback quote from the built-in catalog."""
    item = get_item(catalog_id)
    if item is None:
        return None
    return {
        "catalog_id": catalog_id,
        "source": "catalog",
        "vendor": item["vendor"],
        "title": item["name"],
        "price": item["price"],
        "link": item.get("url"),
        "thumbnail": None,
        "rating": None,
        "reviews": None,
        "fetched_live": False,
    }


def _pick_best_product(products: list[dict], query: str) -> dict | None:
    """Pick the most relevant priced product from SerpApi results.

    Heuristic: among the first 8 results that have a price, prefer ones whose
    title contains the query's key tokens; tie-break on position.
    """
    priced = [p for p in products[:8] if isinstance(p.get("price"), (int, float))]
    if not priced:
        return None
    tokens = [t for t in re.split(r"[\sx/-]+", query.lower()) if len(t) > 1]

    def score(p):
        title = p.get("title", "").lower()
        return sum(1 for t in tokens if t in title)

    return max(priced, key=lambda p: (score(p), -p.get("position", 99)))


async def _serpapi_quote(client: httpx.AsyncClient, catalog_id: str,
                         api_key: str, zip_code: str | None) -> dict | None:
    query = _search_query_for(catalog_id)
    if query is None:
        return None

    cache_key = f"{catalog_id}|{zip_code or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    params = {
        "engine": "home_depot",
        "q": query,
        "api_key": api_key,
        "hd_sort": "best_match",
    }
    if zip_code:
        params["delivery_zip"] = zip_code

    try:
        resp = await client.get(SERPAPI_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None  # caller falls back to catalog

    best = _pick_best_product(data.get("products", []), query)
    if best is None:
        return None

    thumbs = best.get("thumbnails") or [[]]
    quote = {
        "catalog_id": catalog_id,
        "source": "home_depot_live",
        "vendor": "Home Depot",
        "title": best.get("title"),
        "price": round(float(best["price"]), 2),
        "link": best.get("link"),
        "thumbnail": (thumbs[0][0] if thumbs and thumbs[0] else None),
        "rating": best.get("rating"),
        "reviews": best.get("reviews"),
        "fetched_live": True,
    }
    _cache_put(cache_key, quote)
    return quote


# --- public API ----------------------------------------------------------------
def live_pricing_available() -> bool:
    return bool(os.environ.get("SERPAPI_KEY"))


async def get_live_prices(catalog_ids: list[str], zip_code: str | None = None) -> dict:
    """Fetch live quotes for a list of catalog ids.

    Always returns a quote per known id — live when possible, catalog fallback
    otherwise. Response includes whether live pricing was attempted.
    """
    api_key = os.environ.get("SERPAPI_KEY")
    ids = list(dict.fromkeys(catalog_ids))  # dedupe, keep order

    live_quotes: dict[str, dict | None] = {}
    if api_key:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                *[_serpapi_quote(client, cid, api_key, zip_code) for cid in ids]
            )
        live_quotes = dict(zip(ids, results))

    quotes = []
    for cid in ids:
        q = live_quotes.get(cid) or _catalog_quote(cid)
        if q is not None:
            quotes.append(q)

    return {
        "live_enabled": bool(api_key),
        "zip_code": zip_code,
        "quotes": quotes,
    }
