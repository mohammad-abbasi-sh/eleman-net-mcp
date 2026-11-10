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


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport. Added 2026-11-10 (fleet audit fix).
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _r.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise ElemanError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise ElemanError(f"network error fetching {url}: {last_exc}") from last_exc


def _get(url: str) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _request(url, _HEADERS)
    except ElemanError:
        raise
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


def fetch_home_html() -> str:
    """Homepage HTML (used by health_check)."""
    return _get(f"{BASE}/")


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `eleman_health` tool
    and the daily smoke CI. Added 2026-11-10 (fleet audit fix).
    """
    url = "https://www.eleman.net/"
    try:
        fetch_home_html()
    except ElemanError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
