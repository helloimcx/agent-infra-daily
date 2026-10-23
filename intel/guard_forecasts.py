#!/usr/bin/env python3
"""CI change guard: forecasts are pre-registered, not editable hindsight.

Compare the checked-out commit with its first parent. Existing forecast and
resolution objects must remain byte-for-byte equivalent in parsed JSON. Only
new IDs can appear. Reject registrations whose claimed date substantially
predates the committing timestamp. This is a Git history / provenance guard;
it does not certify the truth of editorial evidence or real-world outcomes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import subprocess
from pathlib import Path

FORECASTS = "intel/forecasts.json"
OUTCOMES = "intel/forecast_outcomes.json"
ALLOWED_CLOCK_SKEW = timedelta(hours=2)
MAX_BACKDATE = timedelta(hours=48)


def immutability_errors(before: dict, after: dict, list_name: str, key_name: str) -> list[str]:
    prev = {x[key_name]: x for x in before.get(list_name, [])}
    curr = {x[key_name]: x for x in after.get(list_name, [])}
    errors = []
    if len(prev) != len(before.get(list_name, [])) or len(curr) != len(after.get(list_name, [])):
        errors.append(f"duplicate {key_name} in {list_name}")
    for key, original in prev.items():
        if key not in curr:
            errors.append(f"immutable {list_name} record removed: {key}")
        elif curr[key] != original:
            errors.append(f"immutable {list_name} record edited after publication: {key}")
    return errors


def validate_new_registration_times(before: dict, after: dict,
                                    committed_at: datetime) -> list[str]:
    previous = {x["id"] for x in before.get("forecasts", [])}
    issues = []
    committed_at = committed_at.astimezone(timezone.utc)
    for item in after.get("forecasts", []):
        if item["id"] in previous:
            continue
        try:
            registered = datetime.fromisoformat(item["registered_at"].replace("Z", "+00:00"))
            if registered.tzinfo is None:
                raise ValueError("naive time")
            registered = registered.astimezone(timezone.utc)
            if (committed_at - registered > MAX_BACKDATE or
                registered - committed_at > ALLOWED_CLOCK_SKEW):
                issues.append(f"retroactive/future registration timestamp: {item['id']}")
        except (ValueError, KeyError, TypeError):
            issues.append(f"invalid registration timestamp: {item.get('id')}")
    return issues


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, check=False)


def _read_git(revpath: str) -> dict | None:
    p = _git("show", revpath)
    if p.returncode != 0:
        return None
    return json.loads(p.stdout)


def main() -> None:
    parent = _git("rev-parse", "HEAD^")
    if parent.returncode != 0:
        raise SystemExit("Cannot inspect parent commit; checkout must have fetch-depth>=2")
    old_fc = _read_git("HEAD^:" + FORECASTS) or {"forecasts": []}
    old_out = _read_git("HEAD^:" + OUTCOMES) or {"outcomes": []}
    current_fc = json.loads(Path(FORECASTS).read_text(encoding="utf-8"))
    current_out = json.loads(Path(OUTCOMES).read_text(encoding="utf-8"))
    commit_time = _git("log", "-1", "--format=%cI")
    if commit_time.returncode != 0:
        raise SystemExit("Cannot read commit timestamp")
    committed_at = datetime.fromisoformat(commit_time.stdout.strip())
    problems = (
        immutability_errors(old_fc, current_fc, "forecasts", "id") +
        immutability_errors(old_out, current_out, "outcomes", "forecast_id") +
        validate_new_registration_times(old_fc, current_fc, committed_at)
    )
    if problems:
        raise SystemExit("Forecast preregistration immutability FAILED:\n" +
                         "\n".join("- " + x for x in problems))
    print("Forecast preregistration and past outcome immutability guard passed")


if __name__ == "__main__":
    main()
