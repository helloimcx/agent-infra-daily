import unittest
from datetime import datetime, timezone
from intel.intelligence import merge_snapshot, process, quality
from intel.review import confirm_event, revise_trend

T0 = "2026-10-22T00:30:00+00:00"
T1 = "2026-10-23T00:30:00+00:00"
ITEM1 = {
    "id": "a" * 24, "title": "Cloud agent durable runtime launches official API",
    "source_id": "vendor-blog", "source_kind": "rss", "topic": "runtime",
    "priority": "P1", "url": "https://official.example/first",
    "published_at": "2026-10-21T12:00:00+00:00",
    "first_discovered_at": T0, "evidence_status": "unverified_candidate",
}
ITEM2 = {
    **ITEM1, "id": "b" * 24, "url": "https://other-official.example/first",
    "source_id": "another-official"
}


def snapshot(time=T0, items=None):
    items = items if items is not None else [ITEM1]
    return {
        "beijing_date": time[:10], "generated_at": time,
        "status": "partial", "items": items,
        "source_checks": {
            "ok": [{"id": "vendor-blog", "entries": len(items)}],
            "not_modified": [],
            "errors": [{"id": "unavailable", "error": "HTTP 503"}],
        },
        "event_candidates": [{
            "event_candidate_id": "ec-temp", "representative_title": items[0]["title"],
            "topic": items[0]["topic"], "item_ids": [x["id"] for x in items],
            "source_ids": [x["source_id"] for x in items]
        }] if items else []
    }


def trends():
    return {"trends": [{
        "id": "trend:cloud-agent-runtime",
        "title": "云端Agent持久执行",
        "status": "unassessed", "confidence": "unassessed",
        "evidence_event_ids": [], "history": []
    }]}


class IntelligenceTests(unittest.TestCase):
    def test_cross_day_stable_candidate_and_idempotency(self):
        state = {}
        s = snapshot()
        state = merge_snapshot(s, state, datetime(2026, 10, 22, 0, 40, tzinfo=timezone.utc))
        self.assertEqual(len(state["candidates"]), 1)
        key = next(iter(state["candidates"]))
        state = merge_snapshot(s, state, datetime(2026, 10, 22, 0, 40, tzinfo=timezone.utc))
        self.assertEqual(len(state["candidates"][key]["sources"]), 1)
        later = snapshot(T1, [ITEM2])
        state = merge_snapshot(later, state, datetime(2026, 10, 23, 0, 40, tzinfo=timezone.utc))
        self.assertEqual(len(state["candidates"]), 1)
        self.assertEqual(len(state["candidates"][key]["sources"]), 2)
        self.assertEqual(state["item_index"][ITEM2["id"]], key)

    def test_unverified_signal_does_not_create_event_or_trend_claim(self):
        s = snapshot()
        ledger, report = process(s, {}, {"events": []}, trends(),
                                 datetime(2026, 10, 22, 0, 40, tzinfo=timezone.utc))
        self.assertEqual(len(ledger["candidates"]), 1)
        self.assertEqual(report["curation_metrics"]["verified_events"], 0)
        self.assertEqual(report["curation_metrics"]["hypotheses_with_verified_evidence"], 0)
        self.assertEqual(report["source_health"]["failed"], 1)
        self.assertEqual(report["source_health"]["healthy_fraction"], .5)

    def test_manual_review_requires_real_matching_evidence(self):
        ledger = merge_snapshot(snapshot(), {},
                                datetime(2026, 10, 22, 0, 40, tzinfo=timezone.utc))
        key = next(iter(ledger["candidates"]))
        kwargs = dict(candidate_id=key, title="Cloud Agent durable runtime official announcement",
                      event_date="2026-10-21", selected_item_ids=[ITEM1["id"]],
                      reviewer="research editor", reviewed_at=T0,
                      note="Reviewed the official release post and recorded the scope, technical constraints and event date.")
        with self.assertRaises(ValueError):
            confirm_event(ledger, {"events": []},
                          **dict(kwargs, selected_item_ids=["nonexistent"]))
        events = confirm_event(ledger, {"events": []}, **kwargs)
        self.assertEqual(events["events"][0]["evidence"][0]["url"], ITEM1["url"])
        with self.assertRaisesRegex(ValueError, "event exists"):
            confirm_event(ledger, events, **kwargs)

    def test_trend_requires_verified_new_event(self):
        ledger = merge_snapshot(snapshot(), {},
                                datetime(2026, 10, 22, 0, 40, tzinfo=timezone.utc))
        candidate_id = next(iter(ledger["candidates"]))
        events = confirm_event(
            ledger, {"events": []}, candidate_id=candidate_id,
            title="Cloud Agent runtime official announcement", event_date="2026-10-21",
            selected_item_ids=[ITEM1["id"]], reviewer="research editor", reviewed_at=T0,
            note="Reviewed the original official post and documented the bounded operational claims.")
        event_id = events["events"][0]["id"]
        updates = trends()
        with self.assertRaises(ValueError):
            revise_trend(updates, {"events": []}, trend_id="trend:cloud-agent-runtime",
                         event_ids=[event_id], status="strengthening", confidence="medium",
                         rationale="The vendor introduced another component in the durable execution control plane.",
                         reviewer="research editor", reviewed_at=T0)
        updates = revise_trend(updates, events, trend_id="trend:cloud-agent-runtime",
                               event_ids=[event_id], status="strengthening",
                               confidence="medium", reviewer="research editor",
                               rationale="This first-party source expands official durable execution APIs, but provides no reliability benchmark.",
                               reviewed_at=T0)
        self.assertEqual(updates["trends"][0]["evidence_event_ids"], [event_id])
        with self.assertRaisesRegex(ValueError, "newly verified"):
            revise_trend(updates, events, trend_id="trend:cloud-agent-runtime",
                         event_ids=[event_id], status="strengthening", confidence="medium",
                         rationale="No new independent event has occurred to support another update.",
                         reviewer="research editor", reviewed_at=T1)

    def test_missing_snapshot_is_rejected(self):
        with self.assertRaises(ValueError):
            merge_snapshot({}, {}, datetime.now(timezone.utc))


if __name__ == "__main__":
    unittest.main()
