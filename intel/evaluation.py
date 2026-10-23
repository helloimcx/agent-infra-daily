#!/usr/bin/env python3
"""Evaluate curated gold events against raw unverified ingestion snapshots.

This is a SMALL EDITORIAL SAMPLE AUDIT, not global industry event recall.
Exact primary URL matching avoids inflating coverage from vague title similarity.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

from intel.collector import canonical_url
from intel.intelligence import read, save, utc

REQUIRED = {"id", "title", "event_date_beijing", "primary_url",
            "expected_source_ids", "importance", "reviewed_by",
            "reviewed_at", "verification_notes"}
IMPORTANCE = {"P0", "P1"}


def validate_gold(gold: dict) -> list[str]:
    errors = []
    if gold.get("schema_version") != "1.0":
        errors.append("gold schema_version must be 1.0")
    seen = set()
    urls = set()
    for entry in gold.get("events", []):
        key = entry.get("id", "<missing>")
        if REQUIRED - entry.keys():
            errors.append(f"{key}: missing required fields")
            continue
        if key in seen:
            errors.append(f"{key}: duplicate gold ID")
        seen.add(key)
        url = canonical_url(entry["primary_url"])
        if not url:
            errors.append(f"{key}: invalid HTTPS primary URL")
        elif url in urls:
            errors.append(f"{key}: duplicate primary source URL")
        urls.add(url)
        try:
            date.fromisoformat(entry["event_date_beijing"])
            utc(entry["reviewed_at"])
        except (ValueError, TypeError):
            errors.append(f"{key}: invalid event/review dates")
        if entry["importance"] not in IMPORTANCE:
            errors.append(f"{key}: importance must be P0 or P1")
        if not isinstance(entry["expected_source_ids"], list) or not entry["expected_source_ids"]:
            errors.append(f"{key}: at least one expected source is required")
        if len(entry["verification_notes"].strip()) < 65:
            errors.append(f"{key}: reviewed notes insufficient for editorial gold")
        if len(entry["reviewed_by"].strip()) < 4:
            errors.append(f"{key}: reviewer attribution missing")
    return errors


def evaluate(snapshot: dict, gold: dict, source_config: dict, ledger: dict | None = None) -> dict:
    problems = validate_gold(gold)
    if problems:
        raise ValueError("; ".join(problems))
    now = utc(snapshot["generated_at"])
    window = now - timedelta(hours=int(snapshot.get("lookback_hours", 72)))
    seen_urls = {
        canonical_url(x.get("url", "")): x for x in snapshot.get("items", [])
        if canonical_url(x.get("url", ""))
    }
    historic = {}
    for candidate in (ledger or {}).get("candidates", {}).values():
        for source in candidate.get("sources", []):
            normalized = canonical_url(source.get("url", ""))
            if normalized:
                historic[normalized] = source
    configured = {x["id"] for x in source_config.get("feeds", [])}
    configured |= {"release:" + x["repo"] for x in source_config.get("github_releases", [])}
    configured |= {x["id"] for x in source_config.get("sitemaps", [])}
    configured |= {x["id"] for x in source_config.get("listings", [])}
    results = []
    for event in gold["events"]:
        # Gold event timestamps are grounded in the cited original; day-only
        # granularity is not enough to assert that it falls inside a 72h window.
        # Keep dates as an explicit caveat and evaluate only nearby calendar days.
        event_day = date.fromisoformat(event["event_date_beijing"])
        near_window = window.astimezone(timezone(timedelta(hours=8))).date() - timedelta(days=1)
        within_days = near_window <= event_day <= now.astimezone(timezone(timedelta(hours=8))).date()
        if not within_days:
            continue
        url = canonical_url(event["primary_url"])
        matched = seen_urls.get(url)
        in_scope = bool(configured.intersection(event["expected_source_ids"]))
        if matched:
            outcome = "captured"
        elif in_scope and url in historic:
            outcome = "captured_in_history"
        elif not in_scope:
            outcome = "source_not_monitored"
        else:
            outcome = "in_scope_not_observed"
        results.append({
            "gold_event_id": event["id"], "title": event["title"],
            "event_date_beijing": event_day.isoformat(),
            "importance": event["importance"], "primary_url": url,
            "expected_source_ids": event["expected_source_ids"],
            "in_configured_scope": in_scope, "outcome": outcome,
            "matched_item_id": matched["id"] if matched else
                               (historic.get(url) or {}).get("item_id"),
            "reviewed_at": event["reviewed_at"],
        })
    snapshot_observed = sum(x["outcome"] == "captured" for x in results)
    historical_observed = sum(x["outcome"] == "captured_in_history" for x in results)
    observed = snapshot_observed + historical_observed
    scoped = sum(x["in_configured_scope"] for x in results)
    scoped_observed = sum(x["in_configured_scope"] and x["outcome"] in
                          {"captured", "captured_in_history"} for x in results)
    return {
        "schema_version": "1.0",
        "measurement_kind": "small_editorial_gold_sample_not_industry_recall",
        "snapshot_generated_at": snapshot["generated_at"],
        "beijing_date": snapshot["beijing_date"],
        "gold_sample_size_eligible": len(results),
        "captured_count": observed,
        "snapshot_captured_count": snapshot_observed,
        "historical_captured_count": historical_observed,
        "not_monitored_count": sum(x["outcome"] == "source_not_monitored" for x in results),
        "in_scope_missed_count": sum(x["outcome"] == "in_scope_not_observed" for x in results),
        "sample_capture_fraction": round(observed / len(results), 4) if results else None,
        "in_scope_capture_fraction": round(scoped_observed / scoped, 4) if scoped else None,
        "reviewed_gold_items": results,
        "notes": [
            "These examples were selected editorially and are not a representative sample of all significant Agent Infra events.",
            "Article IDs match exact normalized official URLs, not semantic headlines or syndication.",
            "Gold events have Beijing calendar dates, not always exact timestamps; day-level eligibility is deliberately approximate.",
            "A configured feed may drop a previously captured item from its rolling snapshot. Check the persistent candidate ledger before declaring a miss.",
            "Do not report this value as industry-wide event recall, precision or comprehensive source coverage."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="intel/output/candidates.json")
    parser.add_argument("--gold", default="intel/evaluation/gold_events.json")
    parser.add_argument("--sources", default="intel/sources.json")
    parser.add_argument("--output", default="intel/quality/coverage.json")
    parser.add_argument("--ledger", default="intel/state/candidates.json")
    args = parser.parse_args()
    result = evaluate(read(args.snapshot, {}), read(args.gold, {}),
                      read(args.sources, {}), read(args.ledger, {}))
    save(args.output, result)
    print(f"EDITORIAL GOLD SAMPLE: captured={result['captured_count']}/"
          f"{result['gold_sample_size_eligible']} "
          f"unmonitored={result['not_monitored_count']} "
          f"in_scope_missing={result['in_scope_missed_count']}")


if __name__ == "__main__":
    main()
