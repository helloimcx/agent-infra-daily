import unittest
from datetime import datetime, timezone
from intel.triage import prioritize
from intel.weekly_quality import weekly_report

NOW=datetime(2026,10,23,2,0,tzinfo=timezone.utc)
DATE="2026-10-23T01:00:00+00:00"

def item(i, *, kind="rss", priority="P1", topic="cloud-agent",
         source="official-blog", published=DATE):
    return {
        "id":f"item-{i}","url":f"https://example.org/{i}",
        "title":f"Primary source article {i}","source_id":source,
        "source_kind":kind,"topic":topic,"priority":priority,
        "published_at":published,"evidence_status":"unverified_candidate",
    }

class TriageTests(unittest.TestCase):
    def test_verified_sources_not_recommended_again(self):
        snapshot={"generated_at":DATE,"beijing_date":"2026-10-23",
                  "items":[item(1),item(2),item(3,kind="official_listing",priority="P0",published=None)]}
        ledger={"item_index":{"item-1":"ec-verified","item-2":"ec-next"}}
        events={"events":[{"candidate_id":"ec-verified","status":"verified",
                           "evidence":[{"url":"https://example.org/1"}]}]}
        result=prioritize(snapshot,ledger,events,NOW)
        self.assertEqual(result["count"],2)
        self.assertTrue(all(x["item_id"]!="item-1" for x in result["items"]))
        listing=next(x for x in result["items"] if x["item_id"]=="item-3")
        self.assertIsNone(listing["claimed_published_at"])
        self.assertIn("discovery_only_no_verified_publication_time",listing["review_order_reasons"])

    def test_diversity_caps_and_determinism(self):
        snapshot={"generated_at":DATE,"beijing_date":"2026-10-23",
                  "items":[item(i,priority="P0") for i in range(20)] +
                          [item(30,source="another-vendor",topic="protocol")]}
        first=prioritize(snapshot,{},{"events":[]},NOW)
        second=prioritize(snapshot,{},{"events":[]},NOW)
        self.assertEqual(first,second)
        self.assertEqual(first["source_distribution"]["official-blog"],5)
        self.assertIn("another-vendor",first["source_distribution"])
        self.assertEqual(first["count"],6)

    def test_no_score_fabricates_independent_evidence(self):
        source=item(1,kind="official_listing",published=None)
        result=prioritize({"generated_at":DATE,"items":[source]}, {},{"events":[]},NOW)
        self.assertEqual(result["items"][0]["review_state"],
                         "primary_source_not_yet_verified")
        self.assertEqual(result["scoring_contract"]["method"],
                         "transparent_rules_not_llm")
        with self.assertRaises(ValueError):
            prioritize({"generated_at":DATE,"items":[]},{},{"events":[]},NOW,limit=0)


class WeeklyAuditTests(unittest.TestCase):
    def setUp(self):
        self.events={"events":[
            {"id":"evt-one","title":"Official runtime announced","status":"verified",
             "event_date":"2026-10-22",
             "evidence":[{"url":"https://example.org/event"}],
             "verification":{"reviewed_at":"2026-10-22T11:00:00+00:00"}}]}
        self.trends={"trends":[
            {"id":"trend-one","title":"Control plane", "status":"strengthening",
             "confidence":"low","falsification":"Failure to recover tasks",
             "last_reviewed_at":"2026-10-22T12:00:00+00:00",
             "evidence_event_ids":["evt-one"],
             "history":[{"reviewed_at":"2026-10-22T12:00:00+00:00",
                         "new_evidence_event_ids":["evt-one"]}]},
            {"id":"trend-two","title":"Context isolation","status":"unassessed",
             "confidence":"unassessed","falsification":"No independent gain",
             "history":[],"evidence_event_ids":[]}
        ]}

    def test_weekly_measures_what_is_known_without_fake_signoff(self):
        result=weekly_report(
            NOW, {"generated_at":DATE,"source_health":{"healthy":19,"failed":0}},
            {"gold_sample_size_eligible":3,"captured_count":3,
             "historical_captured_count":1},
            {"candidates":{"a":{},"b":{}}},
            self.events,self.trends,{"items":[{"id":"q"}]},
            {"events":[{"id":"g1"},{"id":"g2"},{"id":"g3"}]})
        self.assertEqual(result["gold_sample"]["curated_sample_size"],3)
        self.assertEqual(result["candidate_backlog"]["current_review_queue"],1)
        self.assertEqual(result["final_editorial_signoff"]["status"],"pending")
        self.assertEqual(len(result["independent_review_audit"]),4)
        self.assertTrue(all(x["status"]=="pending_independent_primary_source_search"
                            for x in result["independent_review_audit"]))
        self.assertEqual(result["trend_calibration"][0]["new_verified_evidence_7d"],["evt-one"])
        self.assertEqual(result["trend_calibration"][1]["review_needed"],True)
        self.assertFalse(result["source_freshness"]["stale"])

    def test_stale_input_visible(self):
        result=weekly_report(NOW, {"generated_at":"2026-10-19T00:00:00Z"},
                             {},{},{"events":[]},{"trends":[]},{},{})
        self.assertTrue(result["source_freshness"]["stale"])
        self.assertEqual(result["gold_sample"]["current_capture_count"],None)
        self.assertIsNone(result["final_editorial_signoff"]["reviewed_at"])

if __name__=="__main__":
    unittest.main()
