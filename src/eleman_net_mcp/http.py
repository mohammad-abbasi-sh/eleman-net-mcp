"""HTTP layer for eleman_net_mcp.

eleman.net serves its job listings fully server-rendered — no login,
no API key, no session cookies. Plain HTTP 200 with a browser UA
(verified live 2026-11-07: /is-ilanlari, /is-ilanlari/garson,
/is-ilani/<slug>-i<id>, city+keyword combos). The transport still
uses curl-cffi chrome120 impersonation, the same proven pattern as
the other Turkey-factory servers. Requests are kept gentle (one at
a time, ~0.8s apart) and read-only.

Search paths (all verified live):
- /is-ilanlari — newest listings, ?sy=N pages (30 cards/page)
- /is-ilanlari/<slug> — position or city slug (garson, istanbul, ...)
- /is-ilanlari/<city-slug>?aranan=<keyword>&arandi=e — city + keyword
- /is-ilani/<slug>-i<id> — job detail (JobPosting JSON-LD)
"""
from __future__ import annotations

import time
from urllib.parse import quote, urlencode

from curl_cffi import requests as _r

BASE = "https://www.eleman.net"
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

_last_fetch = 0.0


class ElemanError(RuntimeError):
    pass


def _get(url: str) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _r.get(url, impersonate="chrome120", headers=_HEADERS, timeout=TIMEOUT)
    except Exception as e:
        raise ElemanError(f"network error fetching {url}: {e}") from e
    finally:
        _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise ElemanError(
            "eleman.net refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise ElemanError(
            "eleman.net rate-limited the request (HTTP 429) — try again later"
        )
    if resp.status_code == 404:
        raise ElemanError(f"page not found (HTTP 404): {url}")
    if resp.status_code != 200:
        raise ElemanError(f"unexpected HTTP {resp.status_code} fetching {url}")
    return resp.text


def fetch_listings(path: str = "", page: int = 1, keyword: str | None = None) -> str:
    """Listing page. path: '' or a position/city slug; keyword adds
    ?aranan=<keyword>&arandi=e (used together with a city slug)."""
    url = f"{BASE}/is-ilanlari"
    if path:
        url += f"/{quote(path)}"
    params: dict[str, str] = {}
    if keyword:
        params["aranan"] = keyword
        params["arandi"] = "e"
    if page and page > 1:
        params["sy"] = str(page)
    if params:
        url += "?" + urlencode(params)
    return _get(url)


def fetch_job_page(path: str) -> str:
    """Job detail page: /is-ilani/<slug>-i<id> (full path or URL)."""
    if path.startswith("http"):
        url = path
    else:
        url = f"{BASE}/{path.lstrip('/')}"
    return _get(url)
