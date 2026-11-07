"""Live tests for eleman_net_mcp — real requests to eleman.net.

Requires network + Chrome TLS impersonation (curl-cffi). The server
is polite by design (~0.8s between requests), so this file takes
~10s. Run: python -m unittest discover -s tests -v

Listings change during the day; tests assert structure and sane
ranges, not exact jobs.
"""
import json
import unittest

from eleman_net_mcp import http as H
from eleman_net_mcp import jobs as J


class TestLiveSearch(unittest.TestCase):
    def test_newest(self):
        html_text = H.fetch_listings()
        data = J.parse_listings(html_text)
        self.assertEqual(len(data["jobs"]), 30)
        self.assertGreater(data["jobs"][0]["job_id"], 0)

    def test_keyword_slug(self):
        html_text = H.fetch_listings("garson")
        data = J.parse_listings(html_text)
        self.assertEqual(len(data["jobs"]), 30)
        titles = " ".join(j["title"] for j in data["jobs"]).lower()
        self.assertIn("garson", titles)

    def test_city_slug(self):
        html_text = H.fetch_listings("istanbul")
        data = J.parse_listings(html_text)
        self.assertEqual(len(data["jobs"]), 30)

    def test_city_and_keyword(self):
        html_text = H.fetch_listings("istanbul", keyword="garson")
        data = J.parse_listings(html_text)
        self.assertEqual(len(data["jobs"]), 30)
        titles = " ".join(j["title"] for j in data["jobs"]).lower()
        self.assertIn("garson", titles)

    def test_page_2(self):
        html_text = H.fetch_listings(page=2)
        data = J.parse_listings(html_text)
        self.assertEqual(len(data["jobs"]), 30)
        self.assertEqual(data["current_page"], 2)


class TestLiveDetail(unittest.TestCase):
    def test_detail(self):
        html_text = H.fetch_listings()
        first = J.parse_listings(html_text)["jobs"][0]
        detail_html = H.fetch_job_page(first["url"])
        d = J.parse_job_detail(detail_html, first["url"])
        # card titles are Title Case, detail titles sentence case —
        # compare case-insensitively
        self.assertEqual(
            J._tr_lower(d["title"]), J._tr_lower(first["title"])
        )
        self.assertTrue(d["date_posted"])
        self.assertTrue(d["company"])
        self.assertTrue(d["description"])

    def test_unknown_job_404(self):
        # unknown slugs 301-redirect to the homepage (HTTP 200); the
        # parse step is what rejects the page (no JobPosting data)
        html_text = H.fetch_job_page("/is-ilani/olmayan-is-i1")
        with self.assertRaises(ValueError):
            J.parse_job_detail(html_text)


class TestLiveSectors(unittest.TestCase):
    def test_sectors(self):
        html_text = H.fetch_listings()
        sectors = J.parse_sectors(html_text)
        self.assertGreaterEqual(len(sectors), 90)

    def test_cities_live(self):
        # spot-check city slugs resolve
        for slug in ("antalya", "sanliurfa", "diyarbakir"):
            html_text = H.fetch_listings(slug)
            data = J.parse_listings(html_text)
            self.assertGreater(len(data["jobs"]), 0, slug)


class TestLiveServerTools(unittest.TestCase):
    """End-to-end: call the MCP tool functions and check JSON output."""

    def test_search_tool(self):
        from eleman_net_mcp.server import eleman_search_jobs

        out = json.loads(eleman_search_jobs(keyword="garson", limit=3))
        self.assertEqual(out["count"], 3)
        self.assertEqual(len(out["jobs"]), 3)
        self.assertIn("garson", out["jobs"][0]["title"].lower()
                      + out["jobs"][0]["url"].lower())

    def test_cities_tool(self):
        from eleman_net_mcp.server import eleman_list_cities

        out = json.loads(eleman_list_cities())
        self.assertEqual(out["count"], 83)

    def test_sectors_tool(self):
        from eleman_net_mcp.server import eleman_list_sectors

        out = json.loads(eleman_list_sectors())
        self.assertGreaterEqual(out["count"], 90)

    def test_bare_id_error(self):
        from eleman_net_mcp.server import eleman_get_job

        out = json.loads(eleman_get_job("4802902"))
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
