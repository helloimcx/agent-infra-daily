#!/usr/bin/env python3
"""Turn daily *unverified* source snapshots into a cross-day candidate ledger.

This module never promotes candidates to facts. Curated events and trend
revisions require explicit editorial verification in review.py.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
import json
from pathlib import Path
import re

SCHEMA = "1.0"
KEEP_DAYS = 90
MAX_CANDIDATES = 2000
MAX_OUTPUT = 180


def utc(value: str) -> datetime:
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("timestamp requires a timezone")
    return date.astimezone(timezone.utc)


def normalize(title: str) -> str:
    return re.sub(r"[\W_]+", " ", title.casefold()).strip()


def similar(left: dict, right: dict) -> bool:
    # Versions are intentionally not grouped by title.
    if left.get("topic") != right.get("topic"):
        return False
    if left.get("source_kind") == "github_release" or right.get("source_kind") == "github_release":
        return False
    ltitle, rtitle = normalize(left["title"]), normalize(right["title"])
    if min(len(ltitle), len(rtitle)) < 24:
        return False
    if left.get("published_at") and right.get("published_at"):
        if abs((utc(left["published_at"]) - utc(right["published_at"])).total_seconds()) > 259200:
            return False
    return SequenceMatcher(None, ltitle, rtitle).ratio() >= 0.94


def merge_snapshot(snapshot: dict, ledger: dict, now: datetime) -> dict:
    """Idempotent merge with stable candidate IDs and a bounded lookback window."""
    if not snapshot.get("generated_at") or not snapshot.get("beijing_date"):
        raise ValueError("snapshot lacks required provenance fields")
    if utc(snapshot["generated_at"]) > now + timedelta(hours=3):
        raise ValueError("snapshot generation time is in the future")
    records = ledger.setdefault("candidates", {})
    recorded_items = ledger.setdefault("item_index", {})
    input_items = {x["id"]: x for x in snapshot.get("items", [])}
    changed = False

    # Cluster suggestions from phase 1 contain only item IDs; they are not facts.
    groups = snapshot.get("event_candidates", [])
    for suggestion in groups:
        children = [input_items[i] for i in suggestion.get("item_ids", []) if i in input_items]
        if not children:
            continue
        children = sorted(children, key=lambda x: x["id"])
        existing_ids = {recorded_items[item["id"]] for item in children if item["id"] in recorded_items}
        matching = sorted(x for x in existing_ids if x in records)
        if matching:
            chosen = matching[0]
        else:
            matches = sorted(
                key for key, entry in records.items()
                if similar(children[0], entry)
            )
            chosen = matches[0] if matches else "ec-" + min(x["id"] for x in children)[:16]
        if chosen not in records:
            first = children[0]
            records[chosen] = {
                "id": chosen, "title": suggestion.get("representative_title") or first["title"],
                "topic": first["topic"], "source_kind": first["source_kind"],
                "published_at": first.get("published_at"),
                "first_seen_at": snapshot["generated_at"],
                "last_seen_at": snapshot["generated_at"],
                "item_ids": [], "sources": [], "status": "unverified_candidate"
            }
            changed = True
        entry = records[chosen]
        for child in children:
            if child["id"] not in entry["item_ids"]:
                entry["item_ids"].append(child["id"])
                changed = True
            if not any(source["item_id"] == child["id"] for source in entry["sources"]):
                entry["sources"].append({
                    "item_id": child["id"], "source_id": child["source_id"],
                    "url": child["url"], "published_at": child.get("published_at"),
                    "title": child["title"], "first_discovered_at": child.get("first_discovered_at")
                })
                changed = True
            recorded_items[child["id"]] = chosen
        entry["item_ids"].sort()
        entry["sources"].sort(key=lambda x: x["item_id"])
        entry["last_seen_at"] = max(entry["last_seen_at"], snapshot["generated_at"])

    # On multiple equivalent groups in the same snapshot, collapse references
    # deterministically; no verified event is altered or inferred.
    for item_id, candidate_id in list(recorded_items.items()):
        if candidate_id not in records:
            recorded_items.pop(item_id)
    cutoff = now - timedelta(days=KEEP_DAYS)
    records = {
        key: value for key, value in records.items()
        if utc(value["last_seen_at"]) >= cutoff
    }
    if len(records) > MAX_CANDIDATES:
        values = sorted(records.values(), key=lambda x: (x["last_seen_at"], x["id"]), reverse=True)
        records = {x["id"]: x for x in values[:MAX_CANDIDATES]}
    ledger["candidates"] = dict(sorted(records.items()))
    ledger["item_index"] = {
        item_id: entry_id for entry_id, entry in ledger["candidates"].items()
        for item_id in entry["item_ids"]
    }
    ledger["schema_version"] = SCHEMA
    ledger["last_ingested_snapshot"] = max(
        ledger.get("last_ingested_snapshot", ""), snapshot["generated_at"])
    return ledger


def quality(snapshot: dict, ledger: dict, events: dict, trends: dict) -> dict:
    checks = snapshot.get("source_checks", {})
    healthy = len(checks.get("ok", [])) + len(checks.get("not_modified", []))
    errors = len(checks.get("errors", []))
    proposals = snapshot.get("event_candidates", [])
    proposal_count = len(proposals)
    items = snapshot.get("items", [])
    clustered = sum(max(0, len(group.get("item_ids", [])) - 1) for group in proposals)
    event_records = events.get("events", [])
    trend_records = trends.get("trends", [])
    # Health / duplicate rate are observable proxies, NOT major-news recall.
    return {
        "schema_version": SCHEMA, "date": snapshot["beijing_date"],
        "generated_at": snapshot["generated_at"],
        "collection_status": snapshot.get("status", "unknown"),
        "source_health": {
            "healthy": healthy, "failed": errors,
            "total": healthy + errors,
            "healthy_fraction": round(healthy / (healthy + errors), 4) if healthy + errors else None,
            "failed_source_ids": [x["id"] for x in checks.get("errors", [])]
        },
        "candidate_metrics": {
            "items_in_snapshot": len(items),
            "clusters_in_snapshot": proposal_count,
            "duplicate_items_clustered": clustered,
            "clustered_fraction": round(clustered / len(items), 4) if items else None,
            "cross_day_candidates_retained": len(ledger["candidates"]),
            "unverified_backlog": len(ledger["candidates"])
        },
        "curation_metrics": {
            "verified_events": len(event_records),
            "tracked_hypotheses": len(trend_records),
            "hypotheses_with_verified_evidence": sum(
                bool(t.get("evidence_event_ids")) for t in trend_records)
        },
        "limitations": [
            "Source health is fetch success, not coverage of all important developments.",
            "Title-based clustering is a conservative duplicate proxy, not semantic event validation.",
            "A source count is not independent corroboration; verified events require primary-source review.",
            "True important-event recall requires a separately curated gold evaluation set."
        ]
    }


def process(snapshot: dict, ledger: dict, events: dict, trends: dict,
            now: datetime) -> tuple[dict, dict]:
    new = merge_snapshot(snapshot, ledger, now)
    return new, quality(snapshot, new, events, trends)


def read(path: str, default: dict) -> dict:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path: str, document: dict) -> None:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
                    encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="intel/output/candidates.json")
    parser.add_argument("--ledger", default="intel/state/candidates.json")
    parser.add_argument("--events", default="intel/events.json")
    parser.add_argument("--trends", default="intel/trends.json")
    parser.add_argument("--quality", default="intel/quality/latest.json")
    args = parser.parse_args()
    snapshot = read(args.snapshot, {})
    ledger = read(args.ledger, {"schema_version": SCHEMA, "candidates": {}, "item_index": {}})
    events = read(args.events, {"events": []})
    trends = read(args.trends, {"trends": []})
    new, metrics = process(snapshot, ledger, events, trends, datetime.now(timezone.utc))
    save(args.ledger, new)
    save(args.quality, metrics)
    print(f"candidate_ledger={len(new['candidates'])} "
          f"verified_events={metrics['curation_metrics']['verified_events']} "
          f"source_health={metrics['source_health']['healthy']}/{metrics['source_health']['total']}")


if __name__ == "__main__":
    main()
