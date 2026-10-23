#!/usr/bin/env python3
"""Daily report delivery contract: verify actual main-branch artifacts and Pages.

Use in GitHub Actions on push and at 11:30 Asia/Shanghai every day.
Does not invent report content or silently pass when Pages is unverified.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import json
from pathlib import Path
import re

DELTA_FIELDS = ("nodes_added","nodes_updated","edges_added","edges_updated")


def check_delivery(root: Path, day: str, runs: dict | None = None,
                   head_sha: str | None = None) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise ValueError("date must use YYYY-MM-DD")
    datetime.strptime(day, "%Y-%m-%d")
    errors = []
    notes = []
    post_path = root / "_posts" / f"{day}-agent-infra-daily.md"
    delta_path = root / "_data" / "kg" / "deltas" / f"{day}.json"
    files = {"post": str(post_path.relative_to(root)),
             "delta": str(delta_path.relative_to(root))}
    if not post_path.is_file():
        errors.append(f"missing daily post: {files['post']}")
    else:
        source = post_path.read_text(encoding="utf-8")
        matches = re.match(r"\A---\n(.*?)\n---\n", source, flags=re.S)
        if not matches:
            errors.append("daily post has missing/invalid YAML front matter")
        else:
            header = matches.group(1)
            for required in ("layout", "title", "date", "summary", "tags"):
                if not re.search(r"^" + re.escape(required) + r":\s*\S", header, re.M):
                    errors.append(f"post front matter missing {required}")
            if not re.search(r"^date:\s*['\"]?" + re.escape(day), header, re.M):
                errors.append("post date does not match Beijing report date")
        if len(source) < 1800:
            errors.append("daily post is unexpectedly short")
        if "今日核心判断" not in source or "Sources" not in source:
            errors.append("daily post missing research judgment or primary Sources")
    if not delta_path.is_file():
        errors.append(f"missing KG delta: {files['delta']}")
    else:
        try:
            delta = json.loads(delta_path.read_text(encoding="utf-8"))
            if delta.get("date") != day:
                errors.append("KG delta date disagrees with report date")
            for key in DELTA_FIELDS:
                if not isinstance(delta.get(key), list):
                    errors.append(f"KG delta missing list: {key}")
        except (OSError, ValueError, TypeError) as exc:
            errors.append("KG delta invalid JSON: " + str(exc))
    pages = {"status": "not_checked", "run_id": None, "conclusion": None}
    if runs is not None:
        if not head_sha:
            errors.append("Pages check requires current main HEAD SHA")
        else:
            matches = [
                r for r in runs.get("workflow_runs", [])
                if r.get("head_sha") == head_sha and
                ("pages build" in r.get("name", "").lower() or
                 "pages deployment" in r.get("name", "").lower())
            ]
            # A run list sorted newest-first; the most recent attempt dominates.
            if matches:
                matched = matches[0]
                pages = {"status": matched.get("status"),
                         "run_id": matched.get("id"),
                         "conclusion": matched.get("conclusion")}
                if matched.get("status") != "completed" or matched.get("conclusion") != "success":
                    errors.append("Pages deployment not confirmed successful for main HEAD: " +
                                  str(pages))
            else:
                errors.append("no Pages deployment run found for main HEAD: " + head_sha)
                pages = {"status": "not_found_for_head", "run_id": None,
                         "conclusion": None}
    else:
        notes.append("Pages not checked in local/push validation; scheduled watchdog must check it.")
    return {"schema_version":"1.0","date":day,"head_sha":head_sha,
            "files":files,"pages":pages,"passed":not errors,
            "errors":errors,"notes":notes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--runs-json")
    ap.add_argument("--head-sha")
    ap.add_argument("--report-json")
    args = ap.parse_args()
    runs = json.loads(Path(args.runs_json).read_text(encoding="utf-8")) if args.runs_json else None
    result = check_delivery(Path(args.repo_root), args.date, runs, args.head_sha)
    body = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report_json:
        target = Path(args.report_json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body + "\n", encoding="utf-8")
    print(body)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
