#!/usr/bin/env python3
"""Deterministic *review queue*, not news credibility or importance prediction.

Promote nothing to the canonical Event/Trend/KG stores. Priorities determine
which original pages a research agent should inspect first; never cite scores
as evidence of significance, novelty, or independent corroboration.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from intel.intelligence import read, save, utc

MAX_REVIEW_QUEUE = 35
TOPIC_CAP = 9
SOURCE_CAP = 5
PRIORITY_POINTS = {"P0": 5, "P1": 2, "P2": 0}


def _score(item: dict, now: datetime) -> tuple[int, list[str]]:
    points = PRIORITY_POINTS.get(item.get("priority"), 0)
    reasons = ["source_catalog_priority:" + str(item.get("priority", "unrated"))]
    kind = item.get("source_kind", "")
    if kind == "github_release":
        points += 2
        reasons.append("official_release_record")
    elif kind in {"rss", "atom"}:
        points += 1
        reasons.append("first_party_feed_record")
    elif kind in {"official_listing", "official_sitemap"}:
        reasons.append("discovery_only_no_verified_publication_time")
    else:
        reasons.append("source_kind_needs_review")
    dt = item.get("published_at")
    if dt and kind not in {"official_listing", "official_sitemap"}:
        try:
            age = (now - utc(dt)).total_seconds() / 3600
        except (ValueError, TypeError):
            age = float("inf")
        if -3 <= age <= 48:
            points += 2
            reasons.append("source_claimed_pubdate_within_48_hours")
        elif 48 < age <= 168:
            points += 1
            reasons.append("source_claimed_pubdate_within_7_days")
    else:
        reasons.append("publication_time_not_verified")
    return points, reasons


def prioritize(snapshot: dict, ledger: dict, events: dict,
               now: datetime, *, limit: int = MAX_REVIEW_QUEUE) -> dict:
    if limit < 1 or limit > 100:
        raise ValueError("review limit must be between 1 and 100")
    if "generated_at" not in snapshot or "items" not in snapshot:
        raise ValueError("candidate snapshot missing provenance")
    verified_ids = {e.get("candidate_id") for e in events.get("events", [])
                    if e.get("status") == "verified"}
    verified_urls = {src.get("url") for event in events.get("events", [])
                     if event.get("status") == "verified"
                     for src in event.get("evidence", [])}
    index = ledger.get("item_index", {})
    ranked = []
    for item in snapshot["items"]:
        if item.get("evidence_status") != "unverified_candidate":
            continue
        if item.get("url") in verified_urls or index.get(item["id"]) in verified_ids:
            continue
        score, reasons = _score(item, now)
        ranked.append({
            "item_id": item["id"], "candidate_id": index.get(item["id"]),
            "title": item["title"], "url": item["url"],
            "source_id": item["source_id"], "source_kind": item["source_kind"],
            "topic": item["topic"], "source_priority": item.get("priority"),
            "claimed_published_at": item.get("published_at"),
            "review_order_score": score, "review_order_reasons": reasons,
            "review_state": "primary_source_not_yet_verified"
        })
    ranked.sort(key=lambda x: (-x["review_order_score"],
                               x["topic"], x["source_id"], x["item_id"]))
    topic_counts, source_counts = {}, {}
    queue = []
    for row in ranked:
        topic = row["topic"]
        source_id = row["source_id"]
        if topic_counts.get(topic, 0) >= TOPIC_CAP or source_counts.get(source_id, 0) >= SOURCE_CAP:
            continue
        queue.append(row)
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        source_counts[source_id] = source_counts.get(source_id, 0) + 1
        if len(queue) >= limit:
            break
    return {
        "schema_version": "1.0",
        "generated_at": now.isoformat(timespec="seconds"),
        "snapshot_generated_at": snapshot["generated_at"],
        "beijing_date": snapshot.get("beijing_date"),
        "kind": "unverified_editorial_review_queue",
        "count": len(queue), "eligible_item_count": len(ranked),
        "topic_distribution": dict(sorted(topic_counts.items())),
        "source_distribution": dict(sorted(source_counts.items())),
        "items": queue,
        "scoring_contract": {
            "method": "transparent_rules_not_llm",
            "source_points": PRIORITY_POINTS,
            "release_bonus": 2, "rss_bonus": 1,
            "recent_claimed_pubdate_bonus_max": 2,
            "topic_cap": TOPIC_CAP, "source_cap": SOURCE_CAP,
            "limit": limit
        },
        "limitations": [
            "Scores prioritize human/research-agent reading, not factual importance, independent evidence, or model confidence.",
            "Publication timestamps are claimed by feeds; sitemap/listing modification dates never become event timestamps.",
            "Not all important events are present in known feeds. Every daily research run must independently search first-party sources.",
            "Top-N review is selection-biased; audit unselected and missed signals separately."
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="intel/output/candidates.json")
    parser.add_argument("--ledger", default="intel/state/candidates.json")
    parser.add_argument("--events", default="intel/events.json")
    parser.add_argument("--output", default="intel/triage/latest.json")
    args = parser.parse_args()
    snapshot = read(args.snapshot, {})
    ledger = read(args.ledger, {})
    events = read(args.events, {"events": []})
    out = prioritize(snapshot, ledger, events, datetime.now(timezone.utc))
    save(args.output, out)
    print(f"review_queue={out['count']}; eligible={out['eligible_item_count']}; "
          f"topics={out['topic_distribution']}")


if __name__ == "__main__":
    main()
