#!/usr/bin/env python3
"""Pre-register falsifiable Agent Infrastructure forecasts and editorial resolutions.

Forecasts are write-once; outcomes live in a separate append-only review file.
Neither a due date nor an RSS article can automatically resolve a forecast.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from urllib.parse import urlsplit

from intel.intelligence import read, save, utc

VERSION = "1.0"
VOID_REASONS = {"criterion_ambiguous", "source_unavailable", "material_scope_change"}


def _day(value: str) -> date:
    return date.fromisoformat(value)


def _verified_events(events: dict) -> dict:
    return {event["id"]: event for event in events.get("events", [])
            if event.get("status") == "verified"}


def register(store: dict, *, trends: dict, events: dict, forecast_id: str,
             trend_id: str, question: str, yes_condition: str, no_condition: str,
             target_date: str, probability: float, baseline_event_ids: list[str],
             baseline_note: str, decision_impact: str, reviewer: str,
             registered_at: str) -> dict:
    """Register once. Updating probabilities or targets retroactively is forbidden."""
    if not forecast_id.startswith("fc-") or len(forecast_id) > 96:
        raise ValueError("forecast IDs must begin with fc- and be <=96 chars")
    if forecast_id in {p["id"] for p in store.get("forecasts", [])}:
        raise ValueError("forecast already registered; write-once")
    if trend_id not in {t["id"] for t in trends.get("trends", [])}:
        raise ValueError("forecast must link to an existing strategic hypothesis")
    if not isinstance(probability, (int, float)) or isinstance(probability, bool) \
            or not 0.01 <= probability <= 0.99:
        raise ValueError("subjective prior must be a probability in [0.01,0.99]")
    register_time = utc(registered_at)
    horizon = (_day(target_date) - register_time.date()).days
    if not 7 <= horizon <= 365:
        raise ValueError("registration-to-target horizon must be 7–365 days")
    for value, n in [(question, 28), (yes_condition, 85), (no_condition, 65),
                     (baseline_note, 70), (decision_impact, 50)]:
        if len(value.strip()) < n:
            raise ValueError("authored forecast criteria/baseline/impact are too short")
    if len(reviewer.strip()) < 4:
        raise ValueError("reviewer required")
    known = _verified_events(events)
    if not baseline_event_ids or len(set(baseline_event_ids)) != len(baseline_event_ids) \
            or not set(baseline_event_ids).issubset(known):
        raise ValueError("forecast baseline requires explicit distinct verified event IDs")
    for eid in baseline_event_ids:
        if _day(known[eid]["event_date"]) > register_time.date():
            raise ValueError("baseline cannot cite an event after registration")
    store.setdefault("forecasts", []).append({
        "id": forecast_id, "trend_id": trend_id,
        "question": question.strip(),
        "yes_condition": yes_condition.strip(),
        "no_condition": no_condition.strip(),
        "target_date": target_date,
        "registered_at": registered_at, "reviewed_by": reviewer.strip(),
        "probability_yes": float(probability),
        "baseline_verified_event_ids": sorted(baseline_event_ids),
        "baseline_note": baseline_note.strip(),
        "decision_impact": decision_impact.strip(),
        "status": "registered",
        "kind": "subjective_falsifiable_prediction_not_observed_fact"
    })
    store["forecasts"].sort(key=lambda e: e["id"])
    store["schema_version"] = VERSION
    return store


def resolve(forecasts: dict, outcomes: dict, *, events: dict,
            forecast_id: str, outcome: str, evidence_event_ids: list[str],
            reviewed_urls: list[str], rationale: str, reviewer: str,
            reviewed_at: str, void_reason: str | None = None) -> dict:
    """Resolve by human/research-agent review only; never from a scheduled job."""
    item = next((p for p in forecasts.get("forecasts", [])
                 if p["id"] == forecast_id), None)
    if item is None:
        raise ValueError("unknown forecast")
    if any(x["forecast_id"] == forecast_id for x in outcomes.get("outcomes", [])):
        raise ValueError("forecast already resolved; preserve resolution history")
    if outcome not in {"yes", "no", "void"}:
        raise ValueError("outcome must be yes/no/void")
    timestamp = utc(reviewed_at)
    target = _day(item["target_date"])
    if timestamp.date() < _day(item["registered_at"][:10]):
        raise ValueError("resolution predates forecast")
    if len(rationale.strip()) < 100 or len(reviewer.strip()) < 4:
        raise ValueError("independently reasoned source review and reviewer required")
    if len(set(reviewed_urls)) != len(reviewed_urls) or any(
            urlsplit(url).scheme != "https" or not urlsplit(url).hostname
            for url in reviewed_urls):
        raise ValueError("review URLs must be unique HTTPS originals")
    available = _verified_events(events)
    if len(set(evidence_event_ids)) != len(evidence_event_ids) \
            or not set(evidence_event_ids).issubset(available):
        raise ValueError("resolution evidence must reference distinct verified canonical events")
    if outcome == "yes":
        if not evidence_event_ids or not reviewed_urls:
            raise ValueError("YES needs a new verified event and independently reviewed primary URL")
        for eid in evidence_event_ids:
            when = _day(available[eid]["event_date"])
            if when < _day(item["registered_at"][:10]) or when > target:
                raise ValueError("YES must have evidence event dated within forecast interval")
        if not set(evidence_event_ids).difference(item["baseline_verified_event_ids"]):
            raise ValueError("baseline evidence alone cannot justify successful outcome")
    elif outcome == "no":
        if timestamp.date() < target:
            raise ValueError("NO may only be resolved at or after the deadline")
        if len(reviewed_urls) < 2:
            raise ValueError("NO needs at least two reviewed primary-source URLs and bounded negative-search methodology")
    else:
        if void_reason not in VOID_REASONS:
            raise ValueError("VOID must disclose a specific adjudicable void reason")
        if not reviewed_urls:
            raise ValueError("VOID needs at least one reviewed URL")
    outcomes.setdefault("outcomes", []).append({
        "forecast_id": forecast_id, "outcome": outcome,
        "void_reason": void_reason if outcome == "void" else None,
        "reviewed_at": reviewed_at, "reviewed_by": reviewer.strip(),
        "evidence_event_ids": sorted(evidence_event_ids),
        "reviewed_primary_urls": sorted(reviewed_urls),
        "rationale": rationale.strip(),
        "kind": "editorial_resolution_not_automatic"
    })
    outcomes["schema_version"] = VERSION
    outcomes["outcomes"].sort(key=lambda e: e["forecast_id"])
    return outcomes


def validate(forecasts: dict, outcomes: dict, events: dict, trends: dict) -> list[str]:
    failures = []
    ids = set()
    trend_ids = {t["id"] for t in trends.get("trends", [])}
    known = _verified_events(events)
    for p in forecasts.get("forecasts", []):
        fid = p.get("id", "")
        if fid in ids or not fid.startswith("fc-"):
            failures.append(f"duplicate/invalid forecast ID {fid}")
        ids.add(fid)
        if p.get("status") != "registered" or p.get("trend_id") not in trend_ids:
            failures.append(f"invalid forecast status or trend {fid}")
        try:
            prob = p["probability_yes"]
            if not isinstance(prob, (int, float)) or isinstance(prob, bool) \
                    or not .01 <= prob <= .99:
                raise ValueError()
            registered = utc(p["registered_at"])
            horizon = (_day(p["target_date"]) - registered.date()).days
            if not 7 <= horizon <= 365:
                raise ValueError()
        except (KeyError, ValueError, TypeError):
            failures.append(f"invalid probability or time window {fid}")
        ids0 = p.get("baseline_verified_event_ids", [])
        if not ids0 or len(set(ids0)) != len(ids0) or not set(ids0).issubset(known):
            failures.append(f"invalid baseline evidence {fid}")
        if any(len(p.get(field, "")) < minimum for field, minimum in (
                ("question", 28), ("yes_condition", 85), ("no_condition", 65),
                ("baseline_note", 70), ("decision_impact", 50))):
            failures.append(f"thin forecast criteria {fid}")
        if not p.get("reviewed_by") or p.get("kind") != "subjective_falsifiable_prediction_not_observed_fact":
            failures.append(f"forecast not editorially registered {fid}")

    reviews = set()
    for o in outcomes.get("outcomes", []):
        fid = o.get("forecast_id")
        if fid in reviews or fid not in ids:
            failures.append(f"orphan/duplicate resolution {fid}")
        reviews.add(fid)
        if o.get("kind") != "editorial_resolution_not_automatic":
            failures.append(f"automated/unknown resolution kind {fid}")
        if not o.get("reviewed_by") or len(o.get("rationale", "")) < 100:
            failures.append(f"unsupported outcome review {fid}")
        if o.get("outcome") not in {"yes", "no", "void"}:
            failures.append(f"unknown outcome {fid}")
        urls = o.get("reviewed_primary_urls", [])
        if not urls or len(urls) != len(set(urls)) or any(
                urlsplit(url).scheme != "https" or not urlsplit(url).hostname for url in urls):
            failures.append(f"invalid reviewed URL list {fid}")
        evidence_ids = o.get("evidence_event_ids", [])
        if len(evidence_ids) != len(set(evidence_ids)) or not set(evidence_ids).issubset(known):
            failures.append(f"missing/retracted outcome evidence {fid}")
        try:
            prediction = next(p for p in forecasts.get("forecasts", []) if p["id"] == fid)
            t = utc(o["reviewed_at"])
            start = _day(prediction["registered_at"][:10])
            deadline = _day(prediction["target_date"])
            if t.date() < start:
                failures.append(f"resolution before registration {fid}")
            if o["outcome"] == "yes" and (not evidence_ids or not set(evidence_ids).difference(
                    prediction["baseline_verified_event_ids"]) or any(
                    not start <= _day(known[eid]["event_date"]) <= deadline
                    for eid in evidence_ids)):
                failures.append(f"YES lacks new in-horizon verified evidence {fid}")
            if o["outcome"] == "no" and (t.date() < deadline or len(urls) < 2):
                failures.append(f"premature/inadequate NO review {fid}")
            if o["outcome"] == "void" and o.get("void_reason") not in VOID_REASONS:
                failures.append(f"invalid VOID rationale {fid}")
        except (StopIteration, KeyError, ValueError, TypeError):
            failures.append(f"resolution date/reference invalid {fid}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Explicit editorial forecast registration/adjudication")
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("register")
    for name in ["forecast-id", "trend-id", "question", "yes-condition",
                 "no-condition", "target-date", "baseline-note", "decision-impact", "reviewer"]:
        create.add_argument("--" + name, required=True)
    create.add_argument("--probability-yes", type=float, required=True)
    create.add_argument("--baseline-event-id", action="append", required=True)
    judge = sub.add_parser("resolve")
    for name in ["forecast-id", "outcome", "rationale", "reviewer"]:
        judge.add_argument("--" + name, required=True)
    judge.add_argument("--evidence-event-id", action="append", default=[])
    judge.add_argument("--reviewed-url", action="append", required=True)
    judge.add_argument("--void-reason", default=None)
    args = parser.parse_args()
    forecasts_path = "intel/forecasts.json"
    outcomes_path = "intel/forecast_outcomes.json"
    forecasts = read(forecasts_path, {"schema_version": VERSION, "forecasts": []})
    outcomes = read(outcomes_path, {"schema_version": VERSION, "outcomes": []})
    events = read("intel/events.json", {"events": []})
    trends = read("intel/trends.json", {"trends": []})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if args.action == "register":
        register(forecasts, trends=trends, events=events,
                 forecast_id=args.forecast_id, trend_id=args.trend_id,
                 question=args.question, yes_condition=args.yes_condition,
                 no_condition=args.no_condition, target_date=args.target_date,
                 probability=args.probability_yes, baseline_event_ids=args.baseline_event_id,
                 baseline_note=args.baseline_note, decision_impact=args.decision_impact,
                 reviewer=args.reviewer, registered_at=now)
        problems = validate(forecasts, outcomes, events, trends)
        if problems:
            raise SystemExit("Invalid forecast:\n" + "\n".join(problems))
        save(forecasts_path, forecasts)
        print("Registered; review Git diff and publish via non-force main fast-forward")
    else:
        resolve(forecasts, outcomes, events=events, forecast_id=args.forecast_id,
                outcome=args.outcome, evidence_event_ids=args.evidence_event_id,
                reviewed_urls=args.reviewed_url, rationale=args.rationale,
                reviewer=args.reviewer, reviewed_at=now, void_reason=args.void_reason)
        problems = validate(forecasts, outcomes, events, trends)
        if problems:
            raise SystemExit("Invalid resolution:\n" + "\n".join(problems))
        save(outcomes_path, outcomes)
        print("Editorial resolution recorded separately; preserve frozen forecast fields")


if __name__ == "__main__":
    main()
