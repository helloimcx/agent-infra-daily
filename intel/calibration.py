#!/usr/bin/env python3
"""Outcome-only calibration. Never infer success or failure from deadline alone.

Brier is calculated exclusively on editorially resolved binary predictions.
A public aggregate is held until >=5 outcomes to avoid a deceptive score.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from intel.intelligence import read, save, utc
from intel.forecasts import validate


def summarize(forecasts: dict, outcomes: dict, events: dict, trends: dict,
              now: datetime) -> dict:
    problems = validate(forecasts, outcomes, events, trends)
    if problems:
        raise ValueError("; ".join(problems))
    now = now.astimezone(timezone.utc)
    reviews = {x["forecast_id"]: x for x in outcomes.get("outcomes", [])}
    open_rows, resolved, voided = [], [], []
    for fc in forecasts.get("forecasts", []):
        rv = reviews.get(fc["id"])
        if rv:
            if rv["outcome"] == "void":
                voided.append({"id": fc["id"], "reason": rv.get("void_reason"),
                               "reviewed_at": rv["reviewed_at"]})
            else:
                resolved.append({"id": fc["id"], "outcome": rv["outcome"],
                                 "predicted_yes": fc["probability_yes"],
                                 "reviewed_at": rv["reviewed_at"],
                                 "brier_component": round((fc["probability_yes"] -
                                     (1 if rv["outcome"] == "yes" else 0))**2, 6)})
            continue
        from datetime import date
        days_remaining = (date.fromisoformat(fc["target_date"]) - now.date()).days
        open_rows.append({
            "id": fc["id"], "trend_id": fc["trend_id"],
            "question": fc["question"], "target_date": fc["target_date"],
            "predicted_yes": fc["probability_yes"],
            "days_remaining": days_remaining,
            "due_for_outcome_review": days_remaining <= 0,
            "status": "registered_not_yet_adjudicated",
        })
    n = len(resolved)
    brier = (round(sum(x["brier_component"] for x in resolved) / n, 4)
             if n >= 5 else None)
    out = {
        "schema_version": "1.0",
        "kind": "editorial_binary_forecast_retrospective",
        "generated_at": now.isoformat(timespec="seconds"),
        "counts": {
            "registered": len(forecasts.get("forecasts", [])),
            "open": len(open_rows), "due_for_review": sum(
                x["due_for_outcome_review"] for x in open_rows),
            "resolved_binary": n, "voided": len(voided)
        },
        "aggregate_brier_score": brier,
        "score_state": ("available_only_for_editorially_resolved_sample"
                        if brier is not None else "insufficient_resolved_sample_minimum_5"),
        "unresolved": open_rows,
        "resolved": resolved,
        "voided": voided,
        "limitations": [
            "Predictions and probabilities were subjective and preregistered; never infer success from news titles.",
            "Overdue forecasts remain open until primary-source adjudication; absence of a captured event is not a negative outcome.",
            "Brier only includes binary yes/no editorial reviews; VOID predictions are shown separately, never counted as correct.",
            "A mean Brier score does not establish calibration or forecasting skill without sufficient, diverse forecasts and comparison baselines.",
            "Zero registered forecasts is an acceptable and truthful initial state."
        ]
    }
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--forecasts", default="intel/forecasts.json")
    p.add_argument("--outcomes", default="intel/forecast_outcomes.json")
    p.add_argument("--events", default="intel/events.json")
    p.add_argument("--trends", default="intel/trends.json")
    p.add_argument("--output", default="intel/quality/forecast_calibration.json")
    args = p.parse_args()
    f = read(args.forecasts, {"forecasts": []})
    o = read(args.outcomes, {"outcomes": []})
    result = summarize(f, o, read(args.events, {"events": []}),
                       read(args.trends, {"trends": []}), datetime.now(timezone.utc))
    save(args.output, result)
    counts = result["counts"]
    print(f"forecasts={counts['registered']} resolved={counts['resolved_binary']} "
          f"due={counts['due_for_review']} brier={result['aggregate_brier_score']}")


if __name__ == "__main__":
    main()
