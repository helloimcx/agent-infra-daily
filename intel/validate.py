#!/usr/bin/env python3
"""Validate the candidate ledger and editor-curated Event/Trend stores.

Separate from, and never relax, scripts/validate_entities.py.
"""
from __future__ import annotations
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlsplit

from intel.evaluation import validate_gold

ROOT = Path("intel")


def check(root: Path = ROOT) -> list[str]:
    errors = []
    def load(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    ledger = load("state/candidates.json")
    events_doc = load("events.json")
    trends_doc = load("trends.json")
    gold = load("evaluation/gold_events.json")
    errors.extend(validate_gold(gold))
    candidates = ledger.get("candidates", {})
    reverse = ledger.get("item_index", {})
    seen = {}
    for cid, candidate in candidates.items():
        if candidate.get("id") != cid or candidate.get("status") != "unverified_candidate":
            errors.append("candidate ID/status mismatch: " + cid)
        source_items = candidate.get("sources", [])
        for s in source_items:
            if s.get("item_id") in seen and seen[s["item_id"]] != cid:
                errors.append("source item referenced by multiple candidates")
            seen[s.get("item_id")] = cid
            if urlsplit(s.get("url", "")).scheme != "https":
                errors.append("candidate source URL must be HTTPS")
    if seen != reverse:
        errors.append("ledger item_index inconsistent with candidates")
    event_ids = set()
    for event in events_doc.get("events", []):
        eid = event.get("id")
        if not eid or eid in event_ids:
            errors.append("duplicate or missing curated event id")
        event_ids.add(eid)
        if event.get("status") not in {"verified", "retracted"}:
            errors.append("invalid event status: " + str(eid))
        try:
            date.fromisoformat(event["event_date"])
        except (ValueError, KeyError):
            errors.append("invalid canonical event date: " + str(eid))
        reviewed = event.get("verification", {})
        if len(reviewed.get("notes", "")) < 35 or not reviewed.get("reviewed_by"):
            errors.append("event lacks substantive source review: " + str(eid))
        source_ids = set()
        for source in event.get("evidence", []):
            if source.get("item_id") in source_ids:
                errors.append("duplicate evidence item: " + str(eid))
            source_ids.add(source.get("item_id"))
            if not source.get("checked_against_primary"):
                errors.append("uncorroborated event evidence item: " + str(eid))
            if urlsplit(source.get("url", "")).scheme != "https":
                errors.append("event evidence URL must be HTTPS: " + str(eid))
        if not source_ids:
            errors.append("canonical event has no first-party reviewed evidence: " + str(eid))
    trend_ids = set()
    verified = {x["id"] for x in events_doc.get("events", []) if x.get("status") == "verified"}
    for trend in trends_doc.get("trends", []):
        tid = trend.get("id")
        if not tid or tid in trend_ids:
            errors.append("duplicate or missing trend id")
        trend_ids.add(tid)
        if trend.get("status") not in {"unassessed", "strengthening", "weakening", "contested", "refuted"}:
            errors.append("invalid trend status: " + str(tid))
        if trend.get("confidence") not in {"unassessed", "low", "medium", "high"}:
            errors.append("invalid trend confidence: " + str(tid))
        if not trend.get("hypothesis") or not trend.get("falsification"):
            errors.append("trend missing authored falsifiability boundary: " + str(tid))
        links = trend.get("evidence_event_ids", [])
        if len(links) != len(set(links)) or not set(links).issubset(verified):
            errors.append("trend references missing/retracted or duplicate evidence: " + str(tid))
        history = trend.get("history", [])
        observed = set()
        for entry in history:
            changes = entry.get("new_evidence_event_ids", [])
            if (not changes or not set(changes).issubset(verified) or observed.intersection(changes)
                or not entry.get("rationale") or not entry.get("reviewed_by")):
                errors.append("invalid or reused trend revision evidence: " + str(tid))
            observed.update(changes)
        if observed != set(links):
            errors.append("trend evidence not justified by revision history: " + str(tid))
    return errors


def main():
    problems = check()
    if problems:
        raise SystemExit("Intel store validation failed:\n" + "\n".join("- " + x for x in problems))
    print("Intel candidate, curated event and trend provenance validation passed")


if __name__ == "__main__":
    main()
