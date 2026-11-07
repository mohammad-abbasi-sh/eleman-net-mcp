"""Stdlib parsing for eleman.net server-rendered pages.

Verified live 2026-11-07 against real pages (fixtures in tests/):
- Listing /is-ilanlari[/<slug>][?sy=N]: 30 job cards per page.
  Each card: <div ... id="ilan_id_<id>"> <a
  href="https://www.eleman.net/is-ilani/<slug>-i<id>"> <h3
  class="c-showcase-box__title ...">Title</h3> ... <span
  class="c-showcase-box__subtitle">Company <br> City - District
  </span> <span class="c-showcase-box__text ...">snippet</span>.
  Pager shows "N / M" (current / total pages).
- Detail /is-ilani/<slug>-i<id>: schema.org JobPosting JSON-LD
  (title, datePosted "2026-11-07 12:57:10", description HTML,
  employmentType, jobLocation addressLocality/addressRegion,
  hiringOrganization name+url+logo, educationRequirements).
  Note: the JobPosting block is the FIRST ld+json script; a second
  BreadcrumbList script follows. Raw JSON may contain control
  characters — parse with a tolerant fallback.
- Sectors sidebar (same listing page): <div id="sektor-search">
  <label><input name="sek[]" value="<id>"/>...<span>Name</span>
  </label> — 93 sectors on the recorded page.
- Popular position/city links: <a
  href="https://www.eleman.net/is-ilanlari/<slug>">Name</a>.
"""
from __future__ import annotations

import html
import json
import re

from . import cities as _C

_TR_UPPER_TO_LOWER = str.maketrans({
    "İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ",
    "Ü": "ü", "Ö": "ö", "Ç": "ç",
})
_TR_LOWER_TO_ASCII = str.maketrans({
    "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "ı": "i",
})


def _tr_lower(s: str) -> str:
    """Turkish-aware lowercase (str.lower() mangles İ -> i + dot)."""
    return s.translate(_TR_UPPER_TO_LOWER).lower()


def slugify(name: str) -> str:
    """Turkish word -> eleman.net URL slug.

    "İstanbul" -> "istanbul", "Şanlıurfa" -> "sanliurfa",
    "Çağrı Merkezi" -> "cagri-merkezi", "Garson" -> "garson".
    """
    s = _tr_lower((name or "").strip()).translate(_TR_LOWER_TO_ASCII)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        raise ValueError(f"cannot slugify {name!r}")
    return s


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- listings

_CARD_START_RE = re.compile(r'id="ilan_id_(\d+)">')
_URL_RE = re.compile(r'href="(https://www\.eleman\.net/is-ilani/[^"]+)"')
_H3_RE = re.compile(r"<h3[^>]*>(.*?)</h3>", re.S)
_SUBTITLE_RE = re.compile(r'c-showcase-box__subtitle">(.*?)</span>', re.S)
_TEXT_SPAN_RE = re.compile(
    r'<span class="c-showcase-box__text[^"]*"[^>]*>(.*?)</span>', re.S
)

_PAGER_RE = re.compile(
    r"<option[^>]*selected[^>]*>(\d+)\s*/\s*(\d+)</option>"
)


def parse_listings(html_text: str) -> dict:
    """Parse a listing page: jobs + pagination info.

    Block-based: each card starts at id="ilan_id_<id>". Cards vary —
    some carry a benefits chip span
    (c-showcase-box__text u-equalize-line-height) before the
    description span, and urgent jobs carry an "ACİL İLAN" badge
    inside the <h3>'s ilantik-grubu div. The title is the text
    before the first <div> in the <h3>; the snippet is the longest
    c-showcase-box__text span in the card.
    """
    jobs: list[dict] = []
    starts = list(_CARD_START_RE.finditer(html_text))
    for idx, m in enumerate(starts):
        job_id = int(m.group(1))
        end = starts[idx + 1].start() if idx + 1 < len(starts) else m.start() + 6000
        block = html_text[m.start():end]
        um = _URL_RE.search(block)
        if not um:
            continue
        hm = _H3_RE.search(block)
        title = _clean(hm.group(1).split("<div")[0]) if hm else ""
        sm = _SUBTITLE_RE.search(block)
        company, location = "", ""
        if sm:
            sub = re.sub(r"<br[^>]*>", "|", sm.group(1))
            parts = [p.strip() for p in _clean(sub).split("|") if p.strip()]
            company = parts[0] if parts else ""
            location = parts[1] if len(parts) > 1 else ""
        snippet = ""
        texts = [_clean(t) for t in _TEXT_SPAN_RE.findall(block)]
        texts = [t for t in texts if t]
        if texts:
            snippet = max(texts, key=len)
        jobs.append({
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "snippet": snippet,
            "url": um.group(1),
        })
    pages = {"current_page": 1, "total_pages": None}
    m = _PAGER_RE.search(html_text)
    if m:
        pages["current_page"] = int(m.group(1))
        pages["total_pages"] = int(m.group(2))
    return {"jobs": jobs, **pages}


def parse_popular_links(html_text: str) -> list[dict]:
    """Popular position/city links: /is-ilanlari/<slug> with a name."""
    out: list[dict] = []
    seen: set[str] = set()
    for slug, name in re.findall(
        r'href="https://www\.eleman\.net/is-ilanlari/([a-z0-9\-]+)"[^>]*>'
        r"(?:<i[^>]*></i>\s*)?([^<]{2,40})<",
        html_text,
    ):
        name = html.unescape(name).strip()
        if slug in seen or not name:
            continue
        seen.add(slug)
        out.append({"name": name, "slug": slug,
                    "url": f"https://www.eleman.net/is-ilanlari/{slug}"})
    return out


def parse_sectors(html_text: str) -> list[dict]:
    """Sector checkboxes from the listing sidebar (name + sek id)."""
    out: list[dict] = []
    seen: set[str] = set()
    for sid, name in re.findall(
        r'name="sek\[\]" value="(\d+)"[^>]*>.*?<span[^>]*>([^<]+)</span>',
        html_text,
        re.S,
    ):
        name = html.unescape(name).strip()
        if sid in seen or not name:
            continue
        seen.add(sid)
        out.append({"sector_id": int(sid), "name": name})
    return out


def list_cities() -> list[dict]:
    """All 81 provinces + the two İstanbul sides, as listing URLs."""
    out: list[dict] = []
    for name in _C.PROVINCES + _C.ISTANBUL_SIDES:
        slug = slugify(name)
        out.append({"name": name, "slug": slug,
                    "url": f"https://www.eleman.net/is-ilanlari/{slug}"})
    return out


# ---------------------------------------------------------------- job detail

_LD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S
)


def _parse_ld(raw: str) -> dict | list | None:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        try:
            return json.loads(re.sub(r"[\x00-\x1f]", " ", raw))
        except (json.JSONDecodeError, ValueError):
            return None


def parse_job_detail(html_text: str, url: str = "") -> dict:
    """Parse a job detail page via its JobPosting JSON-LD block."""
    posting: dict | None = None
    for m in _LD_RE.finditer(html_text):
        data = _parse_ld(m.group(1))
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            posting = data
            break
    if posting is None:
        raise ValueError("no JobPosting data found on this page")
    loc = posting.get("jobLocation") or {}
    addr = loc.get("address") or []
    if isinstance(addr, dict):
        addr = [addr]
    locality = addr[0].get("addressLocality", "") if addr else ""
    region = addr[0].get("addressRegion", "") if addr else ""
    org = posting.get("hiringOrganization") or {}
    edu = posting.get("educationRequirements") or []
    return {
        "title": posting.get("title", ""),
        "date_posted": posting.get("datePosted", ""),
        "employment_type": posting.get("employmentType", ""),
        "description": _clean(posting.get("description", "")),
        "company": org.get("name", ""),
        "company_url": org.get("url", ""),
        "location": locality,
        "region": region,
        "education": [e.get("credentialCategory", "") for e in edu
                      if isinstance(e, dict)],
        "url": url,
    }
