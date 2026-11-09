"""MCP server: unofficial read-only access to eleman.net job listings."""
from __future__ import annotations

import json
import re

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import jobs as _J

mcp = FastMCP("eleman-net-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for eleman.net, Türkiye's blue-collar
job board (#2 jobs site in Türkiye). Data comes from the site's
server-rendered pages — no login, no API key, no session cookies.
Listings: /is-ilanlari (newest, 30 per page, ?sy=N pages) or
/is-ilanlari/<slug> for a position or city slug (garson, sofor,
istanbul, ankara ...); city + keyword combines the city slug with
?aranan=<keyword>&arandi=e. Job detail: /is-ilani/<slug>-i<id>
(schema.org JobPosting: title, datePosted, description,
employmentType, location, company). A bare numeric id is NOT a
valid detail URL — pass the full job URL from a search result.
Sectors: the listing sidebar carries 93 sectors (name + sek id).
Cities: all 81 Turkish provinces (+ the two İstanbul sides) as
/is-ilanlari/<slug> URLs. Read-only; transport uses Chrome TLS
impersonation; requests are spaced ~0.8s apart. Built by Mohammad
Abbasi (mohammad-abbasi-sh) — Turkey MCP factory.\
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir
"""


def _err(e: Exception) -> str:
    return json.dumps({"error": str(e)}, ensure_ascii=False)


def _validate_limit(limit: int, lo: int = 1, hi: int = 30) -> int:
    if not lo <= limit <= hi:
        raise ValueError(f"limit must be between {lo} and {hi}")
    return limit


@mcp.tool()
def eleman_search_jobs(keyword: str | None = None, city: str | None = None,
                       page: int = 1, limit: int = 10) -> str:
    """Search eleman.net jobs. keyword: position/keyword (e.g. "garson",
    "şoför", "muhasebe"); city: Turkish city name (e.g. "İstanbul",
    "Ankara", "İzmir"); page 1..; limit 1..30. Either, both or
    neither may be given (neither = newest listings). Returns jobs
    (id, title, company, location, snippet, URL) + pagination."""
    try:
        if page < 1:
            raise ValueError("page must be >= 1")
        _validate_limit(limit)
        path = ""
        if city:
            path = _J.slugify(city)
        elif keyword:
            path = _J.slugify(keyword)
        html_text = _http.fetch_listings(path, page=page,
                                         keyword=keyword if city else None)
        data = _J.parse_listings(html_text)
    except (ValueError, _http.ElemanError) as e:
        return _err(e)
    return json.dumps(
        {
            "keyword": keyword, "city": city, "page": data["current_page"],
            "total_pages": data["total_pages"],
            "total_on_page": len(data["jobs"]),
            "count": min(limit, len(data["jobs"])),
            "jobs": data["jobs"][:limit],
        },
        ensure_ascii=False,
    )


@mcp.tool()
def eleman_get_job(job_url: str) -> str:
    """Full detail for one eleman.net job. job_url: the job's URL from
    a search result (https://www.eleman.net/is-ilani/<slug>-i<id>) or
    the /is-ilani/<slug>-i<id> path. Returns title, date posted,
    employment type, full description, company (+ URL), location,
    region and education requirements."""
    try:
        if not job_url or not job_url.strip():
            raise ValueError("job_url must not be empty")
        job_url = job_url.strip()
        if re.fullmatch(r"\d+", job_url):
            raise ValueError(
                "a bare job id is not enough — pass the full job URL "
                "from eleman_search_jobs (…/is-ilani/<slug>-i<id>)"
            )
        if not job_url.startswith("http") and not job_url.startswith("/is-ilani/"):
            raise ValueError(
                "job_url must be an eleman.net job URL or /is-ilani/<slug>-i<id> path"
            )
        html_text = _http.fetch_job_page(job_url)
        data = _J.parse_job_detail(html_text, job_url)
    except (ValueError, _http.ElemanError) as e:
        return _err(e)
    return json.dumps(data, ensure_ascii=False)


@mcp.tool()
def eleman_list_sectors() -> str:
    """All job sectors on eleman.net (name + sector id), parsed from
    the site's own listing sidebar. Use a sector name as `keyword`
    in eleman_search_jobs."""
    try:
        html_text = _http.fetch_listings()
        sectors = _J.parse_sectors(html_text)
    except (ValueError, _http.ElemanError) as e:
        return _err(e)
    return json.dumps(
        {"count": len(sectors), "sectors": sectors}, ensure_ascii=False
    )


@mcp.tool()
def eleman_list_cities() -> str:
    """All 81 Turkish provinces (+ the two İstanbul sides) with the
    eleman.net listing URL for each. Use a city name as `city` in
    eleman_search_jobs."""
    return json.dumps(
        {"count": len(_J.list_cities()), "cities": _J.list_cities()},
        ensure_ascii=False,
    )


@mcp.tool()
def eleman_new_listings(limit: int = 10) -> str:
    """The newest job listings on eleman.net (first page, newest
    first). limit 1..30. Returns jobs (id, title, company, location,
    snippet, URL)."""
    try:
        _validate_limit(limit)
        html_text = _http.fetch_listings()
        data = _J.parse_listings(html_text)
    except (ValueError, _http.ElemanError) as e:
        return _err(e)
    return json.dumps(
        {
            "total_on_page": len(data["jobs"]),
            "count": min(limit, len(data["jobs"])),
            "jobs": data["jobs"][:limit],
        },
        ensure_ascii=False,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
