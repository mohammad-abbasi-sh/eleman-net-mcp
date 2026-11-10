# eleman-net-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/eleman-net-mcp

Unofficial **read-only** MCP server for eleman.net, Türkiye's blue-collar job board (#2 jobs site in Türkiye, ~4.4–5.1M visits/month per SimilarWeb) — search jobs by position or city, read full job details, list all 93 sectors and all 81 provinces, and fetch the newest listings.

> Built by Mohammad Abbasi as part of the "Turkey MCP factory" (Sepehr-style pipeline). Not affiliated with eleman.net.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "eleman-net": {
      "command": "uvx",
      "args": ["eleman-net-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m eleman_net_mcp.server` (needs `mcp<2`, `curl-cffi`).

## Tools

| Tool | Description |
|------|-------------|
| `eleman_search_jobs` | Search jobs — `keyword` (position, e.g. "garson", "şoför", "muhasebe"), `city` (e.g. "İstanbul", "Ankara"), `page` 1.., `limit` 1..30; returns jobs (id, title, company, location, snippet, URL) + pagination (197 pages on 2026-11-07) |
| `eleman_get_job` | Full detail for one job — `job_url` (the `…/is-ilani/<slug>-i<id>` URL from a search result); returns title, date posted, employment type, full description, company (+ URL), location, region, education requirements |
| `eleman_list_sectors` | All 93 job sectors on eleman.net (name + sector id), parsed from the site's own listing sidebar |
| `eleman_list_cities` | All 81 Turkish provinces (+ the two İstanbul sides) with the eleman.net listing URL for each |
| `eleman_new_listings` | The newest listings (first page, newest first), `limit` 1..30 |

Example output (`eleman_search_jobs` / keyword "garson"):

```json
{"keyword": "garson", "count": 2, "jobs": [
  {"title": "Garson", "company": "TAVUK DÜNYASI",
   "location": "İstanbul Anadolu - Ataşehir",
   "url": "https://www.eleman.net/is-ilani/…"}, …]}
```

## How it works

eleman.net serves its listings fully server-rendered — no login, no API key, no session cookies. Listing pages carry 30 job cards each (`ilan_id_<id>` blocks: title, company, "City - District", snippet; urgent jobs carry an "ACİL İLAN" badge inside the title block and some cards carry a benefits chip span before the description — the parser handles both). Position and city pages share one slug namespace (`/is-ilanlari/<slug>`: garson, istanbul, ankara …); city + keyword combines the city slug with `?aranan=<keyword>&arandi=e`. Job detail pages carry a schema.org JobPosting JSON-LD block (title, datePosted, description, employmentType, location, company). A bare numeric id is not a valid detail URL — pass the full job URL from a search result (unknown slugs 301-redirect to the homepage, which the parser rejects). Transport uses Chrome TLS impersonation (`curl-cffi`, `chrome120`); requests are spaced ~0.8s apart; everything is read-only.

Note: the site's own `/ara` search and the forum-style search are token-gated, so keyword search goes through the slug/param paths above, which are verified live. The autocomplete endpoint (`/arama_complete.php`) is disallowed in robots.txt and is not used.

## Install

```bash
uvx eleman-net-mcp==0.1.0        # run directly (needs uv)
# or
pip install eleman-net-mcp==0.1.0
eleman-net-mcp    # starts the MCP server on stdio
```

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Offline tests run on recorded fixtures (real pages fetched 2026-11-07); live tests hit eleman.net. 28/28 green at build time (15 offline + 13 live) plus an MCP stdio smoke test.

## Roadmap

- Sector-filtered search (`?sek[]=<id>` filter)
- Company pages (`/firma/<slug>`: company jobs + profile)
- Salary info where the site publishes it (rare in the JobPosting data)

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
