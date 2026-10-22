#!/usr/bin/env python3
"""Explicit editorial promotion of candidate evidence to canonical events/trends.

No model output, RSS item or title cluster can become a verified fact by
running the unattended ingestion job. Each review is a deliberate action.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path

from intel.intelligence import read, save, utc

EVENT_STATUSES = {"verified", "retracted"}
TREND_STATUSES = {"unassessed", "strengthening", "weakening", "contested", "refuted"}
CONFIDENCE = {"low", "medium", "high", "unassessed"}


def confirm_event(ledger: dict, document: dict, *, candidate_id: str,
                  title: str, event_date: str, selected_item_ids: list[str],
                  reviewer: str, note: str, reviewed_at: str) -> dict:
    """Store an authored event with links to explicitly reviewed candidate items."""
    if candidate_id not in ledger.get("candidates", {}):
        raise ValueError("unknown candidate ID")
    candidate = ledger["candidates"][candidate_id]
    if len(title.strip()) < 12 or len(note.strip()) < 35 or len(reviewer.strip()) < 3:
        raise ValueError("title, reviewer, and meaningful verification note are required")
    try:
        parsed = date.fromisoformat(event_date)
    except ValueError:
        raise ValueError("event_date must be ISO YYYY-MM-DD") from None
    if not selected_item_ids:
        raise ValueError("at least one independently reviewed primary source required")
    if len(set(selected_item_ids)) != len(selected_item_ids):
        raise ValueError("duplicate reviewed source item")
    available = {s["item_id"]: s for s in candidate["sources"]}
    if not set(selected_item_ids).issubset(available):
        raise ValueError("reviewed evidence must belong to the selected candidate")
    if parsed > utc(reviewed_at).date():
        raise ValueError("event date cannot be after review date")
    event_id = "evt-" + hashlib.sha256(candidate_id.encode()).hexdigest()[:16]
    events = document.setdefault("events", [])
    if any(e["id"] == event_id for e in events):
        raise ValueError("event exists: amend it explicitly, do not overwrite the original review")
    event = {
        "id": event_id, "candidate_id": candidate_id, "title": title.strip(),
        "topic": candidate["topic"], "event_date": event_date,
        "status": "verified", "kind": "fact_with_editorial_review",
        "evidence": [{**available[i], "checked_against_primary": True}
                     for i in sorted(selected_item_ids)],
        "verification": {"reviewed_at": reviewed_at, "reviewed_by": reviewer.strip(),
                         "notes": note.strip(), "limitations": "Source and event interpretation require periodic re-verification."}
    }
    events.append(event)
    events.sort(key=lambda e: (e["event_date"], e["id"]))
    document["schema_version"] = "1.0"
    return document


def revise_trend(document: dict, events: dict, *, trend_id: str, event_ids: list[str],
                 status: str, confidence: str, rationale: str, reviewer: str,
                 reviewed_at: str) -> dict:
    trends = document.get("trends", [])
    trend = next((t for t in trends if t["id"] == trend_id), None)
    if not trend:
        raise ValueError("unknown trend")
    if status not in TREND_STATUSES or confidence not in CONFIDENCE:
        raise ValueError("invalid status/confidence")
    if len(rationale.strip()) < 45 or len(reviewer.strip()) < 3:
        raise ValueError("substantive rationale and reviewer required")
    valid = {e["id"] for e in events.get("events", []) if e["status"] == "verified"}
    if not event_ids or not set(event_ids).issubset(valid):
        raise ValueError("only verified existing events may support a trend update")
    if len(set(event_ids)) != len(event_ids):
        raise ValueError("duplicate event IDs")
    previous = set(trend.get("evidence_event_ids", []))
    if not set(event_ids) - previous:
        raise ValueError("at least one newly verified event required for a new trend revision")
    revision = {
        "reviewed_at": reviewed_at, "reviewed_by": reviewer.strip(),
        "status": status, "confidence": confidence,
        "new_evidence_event_ids": sorted(event_ids),
        "rationale": rationale.strip()
    }
    trend.setdefault("history", []).append(revision)
    trend["status"] = status
    trend["confidence"] = confidence
    trend["evidence_event_ids"] = sorted(previous.union(event_ids))
    trend["last_reviewed_at"] = reviewed_at
    return document


def main() -> None:
    p = argparse.ArgumentParser(description="Manual/agent-reviewed canonical promotion only")
    sub = p.add_subparsers(dest="action", required=True)
    confirm = sub.add_parser("verify-event")
    confirm.add_argument("--candidate-id", required=True)
    confirm.add_argument("--title", required=True)
    confirm.add_argument("--event-date", required=True)
    confirm.add_argument("--source-item-id", action="append", required=True)
    confirm.add_argument("--reviewer", required=True)
    confirm.add_argument("--notes", required=True)
    confirm.add_argument("--primary-source-checked", action="store_true", required=True)
    update = sub.add_parser("revise-trend")
    update.add_argument("--trend-id", required=True)
    update.add_argument("--event-id", action="append", required=True)
    update.add_argument("--status", choices=sorted(TREND_STATUSES), required=True)
    update.add_argument("--confidence", choices=sorted(CONFIDENCE), required=True)
    update.add_argument("--rationale", required=True)
    update.add_argument("--reviewer", required=True)
    args = p.parse_args()
    ledger_path = "intel/state/candidates.json"
    events_path = "intel/events.json"
    trends_path = "intel/trends.json"
    ledger = read(ledger_path, {})
    events = read(events_path, {"schema_version": "1.0", "events": []})
    trends = read(trends_path, {"schema_version": "1.0", "trends": []})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if args.action == "verify-event":
        updated = confirm_event(ledger, events, candidate_id=args.candidate_id,
                                title=args.title, event_date=args.event_date,
                                selected_item_ids=args.source_item_id,
                                reviewer=args.reviewer, note=args.notes,
                                reviewed_at=now)
        save(events_path, updated)
        print("verified event saved; review diff before committing to main")
    else:
        updated = revise_trend(trends, events, trend_id=args.trend_id,
                               event_ids=args.event_id, status=args.status,
                               confidence=args.confidence,
                               rationale=args.rationale, reviewer=args.reviewer,
                               reviewed_at=now)
        save(trends_path, updated)
        print("trend revision saved; review diff before committing to main")


if __name__ == "__main__":
    main()
