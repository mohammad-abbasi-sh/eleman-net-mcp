"""Offline tests for eleman_net_mcp.jobs — recorded real eleman.net pages.

Fixtures are real pages fetched 2026-11-07 (curl, browser UA):
- listing.html: /is-ilanlari (30 cards; first: Servis Şoförü (Gebze),
  id 4802902, Proteam İnsan Kaynakları, Kocaeli - Gebze; 93 sectors).
- garson.html: /is-ilanlari/garson (30 cards).
- detail.html: /is-ilani/servis-soforu-gebze-i4802902 (JobPosting
  JSON-LD: datePosted 2026-11-07 12:57:10, Dönemsel, Kocaeli/Gebze).
"""
import os
import unittest

from eleman_net_mcp import jobs as J

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(J.slugify("İstanbul"), "istanbul")
        self.assertEqual(J.slugify("Garson"), "garson")
        self.assertEqual(J.slugify("Şanlıurfa"), "sanliurfa")
        self.assertEqual(J.slugify("Çağrı Merkezi"), "cagri-merkezi")
        self.assertEqual(J.slugify("IĞDIR"), "igdir")

    def test_empty(self):
        with self.assertRaises(ValueError):
            J.slugify("   ")


class TestParseListings(unittest.TestCase):
    def setUp(self):
        self.data = J.parse_listings(_read("listing.html"))

    def test_count(self):
        self.assertEqual(len(self.data["jobs"]), 30)

    def test_first_job(self):
        j = self.data["jobs"][0]
        self.assertEqual(j["job_id"], 4802902)
        self.assertEqual(j["title"], "Servis Şoförü (Gebze)")
        self.assertEqual(j["company"], "Proteam İnsan Kaynakları")
        self.assertEqual(j["location"], "Kocaeli - Gebze")
        self.assertEqual(
            j["url"],
            "https://www.eleman.net/is-ilani/servis-soforu-gebze-i4802902",
        )
        self.assertIn("Servis Şoförü", j["snippet"])

    def test_second_job(self):
        j = self.data["jobs"][1]
        self.assertEqual(j["job_id"], 4802899)
        self.assertEqual(j["title"], "Estetisyen")
        self.assertEqual(j["company"], "Queenzz Estetik Ve Güzellik Merkezleri")
        self.assertEqual(j["location"], "Balıkesir - Karesi")

    def test_all_have_fields(self):
        for j in self.data["jobs"]:
            self.assertGreater(j["job_id"], 0)
            self.assertTrue(j["title"])
            self.assertTrue(j["company"])
            self.assertTrue(j["url"].startswith("https://www.eleman.net/is-ilani/"))

    def test_pager(self):
        self.assertEqual(self.data["current_page"], 1)
        self.assertEqual(self.data["total_pages"], 197)


class TestParseGarson(unittest.TestCase):
    def test_garson_page(self):
        data = J.parse_listings(_read("garson.html"))
        self.assertEqual(len(data["jobs"]), 30)
        titles = " ".join(j["title"] for j in data["jobs"]).lower()
        self.assertIn("garson", titles)


class TestParseSectors(unittest.TestCase):
    def test_sectors(self):
        sectors = J.parse_sectors(_read("listing.html"))
        self.assertGreaterEqual(len(sectors), 90)
        by_name = {s["name"]: s["sector_id"] for s in sectors}
        self.assertEqual(by_name["Ahşap"], 103)
        self.assertEqual(by_name["Akvaryum"], 218)
        self.assertIn("Bilişim", by_name)


class TestParsePopularLinks(unittest.TestCase):
    def test_popular(self):
        links = J.parse_popular_links(_read("listing.html"))
        self.assertGreaterEqual(len(links), 30)
        by_slug = {l["slug"]: l["name"] for l in links}
        self.assertEqual(by_slug["garson"], "Garson")
        self.assertEqual(by_slug["istanbul"], "İstanbul")
        self.assertEqual(by_slug["ankara"], "Ankara")


class TestListCities(unittest.TestCase):
    def test_81_provinces(self):
        from eleman_net_mcp.cities import PROVINCES

        self.assertEqual(len(PROVINCES), 81)

    def test_city_rows(self):
        cities = J.list_cities()
        self.assertEqual(len(cities), 83)  # 81 provinces + 2 İstanbul sides
        by_name = {c["name"]: c["slug"] for c in cities}
        self.assertEqual(by_name["İstanbul"], "istanbul")
        self.assertEqual(by_name["Şanlıurfa"], "sanliurfa")
        self.assertEqual(by_name["İstanbul Anadolu"], "istanbul-anadolu")
        self.assertEqual(
            by_name["Diyarbakır"], "diyarbakir"
        )


class TestParseJobDetail(unittest.TestCase):
    def setUp(self):
        self.d = J.parse_job_detail(
            _read("detail.html"),
            "https://www.eleman.net/is-ilani/servis-soforu-gebze-i4802902",
        )

    def test_fields(self):
        self.assertEqual(self.d["title"], "Servis Şoförü (Gebze)")
        self.assertEqual(self.d["date_posted"], "2026-11-07 12:57:10")
        self.assertEqual(self.d["employment_type"], "Dönemsel")
        self.assertEqual(self.d["company"], "Proteam İnsan Kaynakları")
        self.assertEqual(self.d["location"], "Kocaeli,Gebze")
        self.assertEqual(self.d["region"], "Kocaeli")

    def test_description(self):
        self.assertIn("Servis Şoförü arıyoruz", self.d["description"])
        self.assertIn("SRC 2 belgesi", self.d["description"])

    def test_education(self):
        self.assertIn("High School Diploma", self.d["education"])


if __name__ == "__main__":
    unittest.main()
