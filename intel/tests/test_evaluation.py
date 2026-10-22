import unittest
from intel.evaluation import evaluate, validate_gold

GOOD = {
  "schema_version": "1.0",
  "events": [
    {"id": "known-a", "title": "Runtime official launch",
     "event_date_beijing": "2026-10-21",
     "primary_url": "https://example.org/official",
     "expected_source_ids": ["official-feed"],
     "importance": "P0", "reviewed_at": "2026-10-22T06:25:58Z",
     "reviewed_by": "Research reviewer",
     "verification_notes": "The official upstream source was reviewed for exact public event date, product availability, technical claim and limitations; this is a sample only."},
    {"id": "known-b", "title": "Proactive agent preview",
     "event_date_beijing": "2026-10-21",
     "primary_url": "https://not-covered.org/duet",
     "expected_source_ids": ["new-official-source"],
     "importance": "P0", "reviewed_at": "2026-10-22T06:25:58Z",
     "reviewed_by": "Research reviewer",
     "verification_notes": "Checked the vendor primary announcement, preview status, and relevant architecture claims; the production scalability is not established."}
  ]
}
SNAPSHOT = {
  "generated_at": "2026-10-22T06:30:00Z", "beijing_date": "2026-10-22",
  "lookback_hours": 72,
  "items":[{"id":"article-a", "url":"https://example.org/official?utm_source=rss"}]
}
SOURCES = {"feeds":[{"id":"official-feed"}], "github_releases":[]}

class QualityAuditTests(unittest.TestCase):
    def test_sample_gap_vs_in_scope(self):
        result = evaluate(SNAPSHOT, GOOD, SOURCES)
        self.assertEqual(result["gold_sample_size_eligible"], 2)
        self.assertEqual(result["captured_count"], 1)
        self.assertEqual(result["not_monitored_count"], 1)
        self.assertEqual(result["in_scope_missed_count"], 0)
        self.assertEqual(result["sample_capture_fraction"], .5)
        self.assertEqual(result["in_scope_capture_fraction"], 1.0)
        self.assertEqual([x["outcome"] for x in result["reviewed_gold_items"]],
                         ["captured", "source_not_monitored"])

    def test_enabled_source_missing(self):
        result = evaluate({**SNAPSHOT,"items":[]}, GOOD, SOURCES)
        self.assertEqual(result["in_scope_missed_count"], 1)
        self.assertEqual(result["not_monitored_count"], 1)
        self.assertEqual(result["captured_count"], 0)

    def test_gold_duplicate_invalid(self):
        invalid = {**GOOD, "events":[GOOD["events"][0], GOOD["events"][0]]}
        self.assertTrue(validate_gold(invalid))
        invalid2 = {**GOOD, "events":[{**GOOD["events"][0],"verification_notes":"no"}]}
        self.assertTrue(validate_gold(invalid2))

    def test_outside_window_not_scored(self):
        result = evaluate({**SNAPSHOT,"generated_at":"2026-11-10T08:00:00Z"},GOOD,SOURCES)
        self.assertEqual(result["gold_sample_size_eligible"],0)
        self.assertIsNone(result["sample_capture_fraction"])

if __name__=="__main__":
    unittest.main()
