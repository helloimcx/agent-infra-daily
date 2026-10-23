#!/usr/bin/env python3
"""Weekly editorial quality worksheet and trend-hypothesis calibration.

No claims are newly verified here. An independent first-party research pass
is required to complete the weekly audit. Output makes this requirement and
known selection bias explicit; it is NOT self-grading AI intelligence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json

from intel.intelligence import read, save, utc

AUDIT_LANES = [
    ("model_provider_announcements",
     "Independently examine first-party model-provider product and engineering announcements",
     "At least two distinct official vendors, including one outside the current collector top sources"),
    ("cloud_runtime_and_security",
     "Independently inspect cloud runtime, sandbox, identity or tool-gateway provider releases and docs",
     "Use vendor original documentation, not syndicated articles or repository PR lists"),
    ("open_standards_and_research",
     "Independently inspect MCP/A2A primary standards notes, formal research papers and technical reports",
     "Record real protocol publication/revision dates and experimental scope"),
    ("counterexample_and_unknown_source",
     "Seek a major Agent Infrastructure event not mentioned in the current review queue",
     "If none can be identified, record search sources, time window and the uncertain result"),
]

def weekly_report(now: datetime, latest: dict, coverage: dict, ledger: dict,
                  events: dict, trends: dict, triage: dict, gold: dict,
                  forecast_calibration: dict | None = None) -> dict:
    now = now.astimezone(timezone.utc)
    start = now - timedelta(days=7)
    if latest.get("generated_at"):
        age_hours = (now - utc(latest["generated_at"])).total_seconds() / 3600
    else:
        age_hours = None
    verified = {e["id"]: e for e in events.get("events", [])
                if e.get("status") == "verified"}
    recent_events = [
        {"id": e["id"], "title": e["title"], "event_date": e["event_date"],
         "source_urls": [s["url"] for s in e.get("evidence", [])]}
        for e in verified.values()
        if e.get("verification", {}).get("reviewed_at") and
           start <= utc(e["verification"]["reviewed_at"]) <= now
    ]
    topics = []
    for item in trends.get("trends", []):
        history = item.get("history", [])
        valid_updates = [row for row in history
                         if row.get("reviewed_at") and
                         start <= utc(row["reviewed_at"]) <= now]
        last = item.get("last_reviewed_at")
        review_age = ((now - utc(last)).days if last else None)
        topics.append({
            "id": item["id"], "title": item["title"],
            "status": item.get("status"), "confidence": item.get("confidence"),
            "evidence_count": len(item.get("evidence_event_ids", [])),
            "new_verified_evidence_7d": sorted({
                eid for row in valid_updates
                for eid in row.get("new_evidence_event_ids", [])
                if eid in verified
            }),
            "new_revisions_7d": len(valid_updates),
            "days_since_review": review_age,
            "falsification": item.get("falsification"),
            "review_needed": (review_age is None or review_age >= 30),
            "calibration_state": (
                "evidence_reviewed_this_week" if valid_updates
                else "no_new_verified_change_in_store"),
            "caveat": "This checks stored review history, not empirical prediction accuracy."
        })
    iso = now.astimezone(timezone(timedelta(hours=8))).isocalendar()
    week = f"{iso.year}-W{iso.week:02d}"
    audit = [{
        "lane": lane, "instruction": task, "evidence_requirements": requirement,
        "status": "pending_independent_primary_source_search",
        "first_party_urls_checked": [],
        "events_found_outside_existing_candidates": [],
        "editorial_notes": ""
    } for lane, task, requirement in AUDIT_LANES]
    return {
        "schema_version": "1.0",
        "week_beijing": week,
        "generated_at": now.isoformat(timespec="seconds"),
        "kind": "weekly_audit_worksheet_not_completed_research",
        "source_freshness": {
            "latest_snapshot_at": latest.get("generated_at"),
            "age_hours": round(age_hours, 2) if age_hours is not None else None,
            "stale": age_hours is None or age_hours < -1 or age_hours >= 36,
            "last_source_health": latest.get("source_health", {}),
        },
        "candidate_backlog": {
            "cross_day_groups": len(ledger.get("candidates", {})),
            "current_review_queue": len(triage.get("items", [])),
            "queue_method": triage.get("kind"),
            "review_queue_is_a_sample_not_global_coverage": True,
        },
        "gold_sample": {
            "curated_sample_size": len(gold.get("events", [])),
            "eligible_current_evaluation_count": coverage.get("gold_sample_size_eligible"),
            "current_capture_count": coverage.get("captured_count"),
            "historical_capture_count": coverage.get("historical_captured_count"),
            "note": "Hand-picked examples are biased. These are not industry recall estimates."
        },
        "verified_events_reviewed_last_7d": recent_events,
        "trend_calibration": topics,
        "forecast_retrospective": {
            "counts": (forecast_calibration or {}).get("counts", {}),
            "aggregate_brier_score": (forecast_calibration or {}).get("aggregate_brier_score"),
            "score_state": (forecast_calibration or {}).get("score_state", "not_available"),
            "note": "Overdue predicts need evidence review; no automatic resolution or claimed skill."
        },
        "independent_review_audit": audit,
        "final_editorial_signoff": {
            "status": "pending",
            "reviewer": None,
            "reviewed_at": None,
            "number_of_independently_found_events": None,
            "genuine_feed_gaps": [],
            "retrospective_overconfidence_findings": [],
            "decision_changes": []
        },
        "limitations": [
            "Generation of a worksheet is not completion of an independent weekly research audit.",
            "No trend accuracy metric exists until reviewed time-bounded predictions/outcomes are retained.",
            "A week with zero changes in the curated store does not prove there were no industry changes.",
            "RSS source failures, missing dates and biased gold selection must remain visible."
        ]
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--latest", default="intel/quality/latest.json")
    p.add_argument("--coverage", default="intel/quality/coverage.json")
    p.add_argument("--ledger", default="intel/state/candidates.json")
    p.add_argument("--events", default="intel/events.json")
    p.add_argument("--trends", default="intel/trends.json")
    p.add_argument("--triage", default="intel/triage/latest.json")
    p.add_argument("--gold", default="intel/evaluation/gold_events.json")
    p.add_argument("--output", default=None)
    args = p.parse_args()
    result = weekly_report(
        datetime.now(timezone.utc),
        read(args.latest, {}), read(args.coverage, {}),
        read(args.ledger, {}), read(args.events, {"events": []}),
        read(args.trends, {"trends": []}), read(args.triage, {}),
        read(args.gold, {"events": []}),
        read("intel/quality/forecast_calibration.json", {}))
    path = args.output or ("intel/weekly/" + result["week_beijing"] + ".json")
    save(path, result)
    print(f"weekly_worksheet={result['week_beijing']}; "
          f"review_lanes={len(result['independent_review_audit'])}; "
          f"verified_events_last_7d={len(result['verified_events_reviewed_last_7d'])}; "
          f"stale_source_data={result['source_freshness']['stale']}")


if __name__ == "__main__":
    main()
