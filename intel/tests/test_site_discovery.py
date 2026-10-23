import unittest
from datetime import datetime,timezone
from intel.site_discovery import sitemap_discovery, page_title
from intel.collector import collect, stamp, make_item

NOW=datetime(2026,10,23,1,0,tzinfo=timezone.utc)
SRC={"id":"claude-product","url":"https://claude.com/sitemap.xml","topic":"cloud-agent","priority":"P0","include_prefixes":["/resources/articles/"]}
INDEX=b"""<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>https://claude.com/sitemap-products.xml</loc></sitemap></sitemapindex>"""
PAGES=b"""<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://claude.com/resources/articles/claude-duet</loc><lastmod>2026-10-22T14:00:00Z</lastmod></url>
<url><loc>https://claude.com/resources/articles/old</loc><lastmod>2026-01-01</lastmod></url>
<url><loc>https://claude.com/unrelated</loc><lastmod>2026-10-22T12:00:00Z</lastmod></url>
<url><loc>https://evil.test/resources/articles/fake</loc><lastmod>2026-10-22</lastmod></url>
<url><loc>https://claude.com/resources/articles/no-date</loc></url>
</urlset>"""

class SiteDiscoveryTests(unittest.TestCase):
    def fixture(self,url,headers):
        return (INDEX if url.endswith("sitemap.xml") else PAGES),200,{}

    def test_exact_host_recent_allowlist(self):
        found,warnings=sitemap_discovery(SRC,NOW,self.fixture,stamp,make_item)
        self.assertFalse(warnings)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["url"],"https://claude.com/resources/articles/claude-duet")
        self.assertIsNone(found[0]["published_at"])
        self.assertEqual(found[0]["date_basis"],"site_lastmod_not_publication")
        self.assertTrue(found[0]["title"].startswith("Official site update:"))

    def test_source_ingestion_preserves_provenance(self):
        state,run=collect({"sitemaps":[SRC]}, {}, NOW, self.fixture)
        self.assertEqual(run["status"],"ok")
        self.assertEqual(run["item_count"],1)
        self.assertEqual(run["items"][0]["source_id"],"claude-product")
        self.assertEqual(run["source_checks"]["ok"][0]["id"],"claude-product")
        self.assertEqual(len(state["items"]),1)

    def test_cross_host_child_does_not_execute(self):
        xml=INDEX.replace(b"https://claude.com/sitemap-products.xml",
                          b"https://untrusted.test/sitemap.xml")
        calls=[]
        def inject(url,headers):
            calls.append(url)
            return (xml if url.endswith("/sitemap.xml") else PAGES),200,{}
        found,warnings=sitemap_discovery(SRC,NOW,inject,stamp,make_item)
        self.assertFalse(found)
        self.assertEqual(len(calls),1)
        self.assertTrue(any("cross-origin" in x for x in warnings))

    def test_entity_payload_rejected(self):
        def evil(url,headers):
            return b'<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><urlset/>',200,{}
        with self.assertRaisesRegex(ValueError,"DTD"):
            sitemap_discovery(SRC,NOW,evil,stamp,make_item)

if __name__=="__main__":
    unittest.main()
