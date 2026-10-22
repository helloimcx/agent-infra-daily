import json
import unittest
from datetime import datetime, timezone
from intel.collector import (canonical_url, candidate_events, collect,
                             parse_feed, parse_releases)

NOW = datetime(2026, 10, 22, 0, 30, tzinfo=timezone.utc)
SOURCE = {"id": "official", "topic": "runtime", "priority": "P1"}
RSS = b"""<rss version="2.0"><channel><title>Official</title>
<item><title>Durable execution platform announced</title>
<link>https://example.org/story?utm_source=x</link>
<pubDate>Wed, 21 Oct 2026 12:00:00 GMT</pubDate><description>Primary announcement</description></item>
</channel></rss>"""
ATOM = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<title>Sandbox backend announcement</title>
<link rel="alternate" href="https://example.org/sandbox"/>
<updated>2026-10-21T16:00:00Z</updated><summary>Engineering notes</summary>
</entry></feed>"""


class CollectorTests(unittest.TestCase):
    def test_url_normalization(self):
        self.assertEqual(canonical_url("https://EXAMPLE.org/story/?utm_source=x&b=2&a=1#test"),
                         "https://example.org/story?a=1&b=2")
        self.assertIsNone(canonical_url("http://example.org/a"))
        self.assertIsNone(canonical_url("https://user:pass@example.org/a"))

    def test_rss_atom_and_xml_safety(self):
        self.assertEqual(parse_feed(RSS, SOURCE, NOW.isoformat())[0]["title"],
                         "Durable execution platform announced")
        self.assertEqual(parse_feed(ATOM, SOURCE, NOW.isoformat())[0]["published_at"],
                         "2026-10-21T16:00:00+00:00")
        with self.assertRaises(ValueError):
            parse_feed(b'<!DOCTYPE foo><rss/>', SOURCE, NOW.isoformat())

    def test_releases_exclude_prerelease(self):
        body = json.dumps([
            {"name": "v1.0", "tag_name": "v1.0",
             "html_url": "https://github.com/x/y/releases/tag/v1.0",
             "published_at": "2026-10-21T15:00:00Z", "draft": False, "prerelease": False},
            {"name": "v1.1-rc", "html_url": "https://github.com/x/y/releases/tag/rc",
             "draft": False, "prerelease": True},
        ]).encode()
        self.assertEqual(len(parse_releases(body, SOURCE, NOW.isoformat())), 1)

    def test_incremental_etag_and_no_duplicates(self):
        config = {"feeds": [{"id": "official", "url": "https://example.org/rss",
                             "topic": "runtime", "priority": "P1"}]}
        state, snapshot = collect(config, {}, NOW, lambda u, h: (RSS, 200, {"etag": '"v1"'}))
        self.assertEqual(snapshot["item_count"], 1)
        self.assertEqual(len(state["items"]), 1)
        def cached(url, headers):
            self.assertEqual(headers["If-None-Match"], '"v1"')
            return None, 304, {}
        state, snapshot = collect(config, state, NOW, cached)
        self.assertEqual(snapshot["item_count"], 1)
        self.assertEqual(len(state["items"]), 1)

    def test_partial_failure_retains_history(self):
        config = {"feeds": [{"id": "official", "url": "https://example.org/rss",
                             "topic": "runtime", "priority": "P1"}]}
        state, _ = collect(config, {}, NOW, lambda u, h: (RSS, 200, {}))
        def failing(url, headers):
            raise RuntimeError("HTTP 503")
        state, snapshot = collect(config, state, NOW, failing)
        self.assertEqual(snapshot["status"], "partial")
        self.assertEqual(snapshot["item_count"], 1)
        self.assertEqual(len(snapshot["source_checks"]["errors"]), 1)

    def test_cluster_is_only_a_candidate_and_releases_stay_separate(self):
        item = {"id": "a", "source_id": "s1",
                "title": "Managed Agent runtime adds secure capability registry",
                "topic": "runtime", "source_kind": "rss",
                "published_at": "2026-10-21T12:00:00+00:00"}
        sibling = dict(item, id="b", source_id="s2")
        self.assertEqual(len(candidate_events([item, sibling])), 1)
        self.assertEqual(len(candidate_events([
            dict(item, source_kind="github_release"),
            dict(sibling, source_kind="github_release")])), 2)


if __name__ == "__main__":
    unittest.main()
