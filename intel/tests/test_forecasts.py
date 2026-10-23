import unittest
from datetime import datetime, timezone

from intel.forecasts import register, resolve, validate
from intel.calibration import summarize

T0="2026-10-23T02:20:00+00:00"
AFTER="2026-11-05T12:00:00+00:00"
LATE="2026-11-12T12:00:00+00:00"

EVENTS={"events":[
    {"id":"evt-baseline","event_date":"2026-10-21","status":"verified"},
    {"id":"evt-new","event_date":"2026-11-04","status":"verified"},
    {"id":"evt-later","event_date":"2026-11-16","status":"verified"},
]}
TRENDS={"trends":[{"id":"trend:tool-governance"}]}
QUESTION="Will documented runtime policy enforcement reach the required capability threshold?"
YES=("YES if an official upstream specification or general-availability product documentation "
     "explicitly defines revocable task-scoped authorization with an operational audit trace before the target date.")
NO=("NO otherwise, after verifying first-party release and specification histories "
    "of the identified vendors during the complete registration-to-deadline interval.")
BASELINE=("The existing reviewed registry announcement documents dynamic tool discovery "
          "but not cross-vendor authorization continuity under task resumption.")
IMPACT=("If yes, prototype a common policy gateway; otherwise continue provider-specific "
        "connectors and preserve a replaceable tool-authorization boundary.")
RATIONALE=("Verified the official first-party release document in detail, checked the exact "
           "capability boundary and registration-to-deadline event date, and noted that "
           "no independent enterprise-scale reliability data has yet been published.")


def registered(identifier="fc-test"):
    return register(
        {"forecasts":[]}, trends=TRENDS, events=EVENTS,
        forecast_id=identifier, trend_id="trend:tool-governance",
        question=QUESTION, yes_condition=YES, no_condition=NO,
        target_date="2026-11-10", probability=.65,
        baseline_event_ids=["evt-baseline"], baseline_note=BASELINE,
        decision_impact=IMPACT, reviewer="research reviewer", registered_at=T0)


class ForecastLedgerTests(unittest.TestCase):
    def test_register_is_write_once_with_frozen_criteria(self):
        doc=registered()
        self.assertEqual(doc["forecasts"][0]["probability_yes"], .65)
        self.assertEqual(validate(doc,{"outcomes":[]},EVENTS,TRENDS),[])
        with self.assertRaisesRegex(ValueError,"write-once"):
            register(doc,trends=TRENDS,events=EVENTS,forecast_id="fc-test",
                     trend_id="trend:tool-governance",question=QUESTION,
                     yes_condition=YES,no_condition=NO,target_date="2026-11-10",
                     probability=.91,baseline_event_ids=["evt-baseline"],
                     baseline_note=BASELINE,decision_impact=IMPACT,
                     reviewer="research reviewer",registered_at=T0)

    def test_cannot_resolve_no_before_deadline(self):
        with self.assertRaisesRegex(ValueError,"deadline"):
            resolve(registered(),{"outcomes":[]},events=EVENTS,
                    forecast_id="fc-test",outcome="no",
                    evidence_event_ids=[],reviewed_urls=[
                        "https://official.example/releases",
                        "https://other.example/specifications"],
                    rationale=RATIONALE,reviewer="research reviewer",reviewed_at=AFTER)

    def test_yes_must_use_new_time_bounded_verified_evidence(self):
        doc=registered()
        for ids in (["evt-baseline"],["evt-later"]):
            with self.assertRaises(ValueError):
                resolve(doc,{"outcomes":[]},events=EVENTS,forecast_id="fc-test",
                        outcome="yes",evidence_event_ids=ids,
                        reviewed_urls=["https://official.example/announcement"],
                        rationale=RATIONALE,reviewer="research reviewer",
                        reviewed_at=AFTER)
        resolved=resolve(doc,{"outcomes":[]},events=EVENTS,forecast_id="fc-test",
                         outcome="yes",evidence_event_ids=["evt-new"],
                         reviewed_urls=["https://official.example/announcement"],
                         rationale=RATIONALE,reviewer="research reviewer",reviewed_at=AFTER)
        self.assertEqual(validate(doc,resolved,EVENTS,TRENDS),[])
        with self.assertRaisesRegex(ValueError,"already resolved"):
            resolve(doc,resolved,events=EVENTS,forecast_id="fc-test",
                    outcome="no",evidence_event_ids=[],
                    reviewed_urls=["https://x.example/a","https://y.example/b"],
                    rationale=RATIONALE,reviewer="research reviewer",reviewed_at=LATE)

    def test_brier_minimum_only_on_resolution(self):
        doc=registered()
        pending=summarize(doc,{"outcomes":[]},EVENTS,TRENDS,
                          datetime(2026,11,12,tzinfo=timezone.utc))
        self.assertEqual(pending["counts"]["due_for_review"],1)
        self.assertEqual(pending["counts"]["resolved_binary"],0)
        self.assertIsNone(pending["aggregate_brier_score"])
        done=resolve(doc,{"outcomes":[]},events=EVENTS,forecast_id="fc-test",
                     outcome="yes",evidence_event_ids=["evt-new"],
                     reviewed_urls=["https://official.example/announcement"],
                     rationale=RATIONALE,reviewer="research reviewer",reviewed_at=AFTER)
        score=summarize(doc,done,EVENTS,TRENDS,
                        datetime(2026,11,12,tzinfo=timezone.utc))
        self.assertEqual(score["counts"]["resolved_binary"],1)
        self.assertIsNone(score["aggregate_brier_score"])
        for i in range(1,5):
            part=registered(f"fc-test-{i}")
            doc["forecasts"].extend(part["forecasts"])
            new=resolve(part,{"outcomes":[]},events=EVENTS,
                        forecast_id=f"fc-test-{i}",outcome="yes",
                        evidence_event_ids=["evt-new"],
                        reviewed_urls=["https://official.example/announcement"],
                        rationale=RATIONALE,reviewer="research reviewer",
                        reviewed_at=AFTER)
            done["outcomes"].extend(new["outcomes"])
        score=summarize(doc,done,EVENTS,TRENDS,
                        datetime(2026,11,12,tzinfo=timezone.utc))
        self.assertEqual(score["counts"]["resolved_binary"],5)
        self.assertAlmostEqual(score["aggregate_brier_score"],.1225)

    def test_void_separate_from_scored_outcomes(self):
        doc=registered()
        resolution=resolve(doc,{"outcomes":[]},events=EVENTS,
                           forecast_id="fc-test",outcome="void",evidence_event_ids=[],
                           reviewed_urls=["https://official.example/spec"],
                           void_reason="criterion_ambiguous",
                           rationale=RATIONALE,reviewer="research reviewer",
                           reviewed_at=AFTER)
        summary=summarize(doc,resolution,EVENTS,TRENDS,
                          datetime(2026,11,12,tzinfo=timezone.utc))
        self.assertEqual(summary["counts"]["voided"],1)
        self.assertEqual(summary["counts"]["resolved_binary"],0)


if __name__ == "__main__":
    unittest.main()
